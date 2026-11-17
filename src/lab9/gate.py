"""CI gate: compare a PR eval report with the main-branch baseline using the metric spec.

    python -m lab9.gate --pr reports/eval_workflow.json --baseline reports/baseline_v1.json

exit 0 = merge, exit 1 = blocked. Safety metrics: max 0, no averaging away.
Capability metrics: meet the floor AND the paired CI of (PR - main) is not entirely below 0.
Thresholds may only get stricter on the same eval-set version (ratchet).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from lab8.console import utf8_stdio
from lab9 import stats
from lab9.eval import SPEC, load_spec, per_item


def integrity_check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> list[str]:
    """M7 (Expert): refuse to compare reports that cannot be trusted. Return a list of problems
    (empty = trustworthy). A gate that passes a broken report is worse than no gate.
    Must catch at least:
      - any metric value in pr["metrics"] that is NaN or inf
      - len(pr["rows"]) != manifest items x len(manifest seeds)   (dropped / duplicated rows)
      - the (item_id, seed) set of PR differs from the baseline's (cherry-picked seeds/items)
      - pr["evaluator_failures"] non-empty, or a row whose value for a graded spec metric is
        None (a crashed grader silently scores as "missing" and drops out of the mean)
      - base_spec given and a threshold in spec is LOOSER than in base_spec for the same
        eval-set version (ratchet: max may not rise, min may not fall, a blocking metric may
        not become non-blocking, a metric may not disappear; the same for spec["slices"],
        including dropping no_significant_drop)
      - an item's slice tags in PR rows differ from the baseline's (relabelling an item out of a
        slice hides its regression from the slice gate)"""
    import math as _math

    problems: list[str] = []

    for mid, val in (pr.get("metrics") or {}).items():
        if isinstance(val, (int, float)) and (_math.isnan(val) or _math.isinf(val)):
            problems.append(f"metric {mid} is NaN/inf: {val}")

    manifest = pr.get("manifest") or {}
    want_rows = manifest.get("items", 0) * len(manifest.get("seeds") or [])
    if want_rows and len(pr.get("rows") or []) != want_rows:
        problems.append(f"row count {len(pr.get('rows') or [])} != manifest {manifest.get('items')} items x "
                        f"{len(manifest.get('seeds') or [])} seeds = {want_rows}")

    def keyset(report: dict) -> set[tuple]:
        return {(r.get("item_id"), r.get("seed")) for r in report.get("rows") or []}

    pr_keys, base_keys = keyset(pr), keyset(base)
    if pr_keys != base_keys:
        missing = sorted(base_keys - pr_keys)
        extra = sorted(pr_keys - base_keys)
        if missing:
            problems.append(f"dropped (item_id, seed) rows vs baseline: {missing[:5]}")
        if extra:
            problems.append(f"extra/cherry-picked (item_id, seed) rows not in baseline: {extra[:5]}")

    if pr.get("evaluator_failures"):
        problems.append(f"{len(pr['evaluator_failures'])} evaluator_failures: {pr['evaluator_failures'][:3]}")

    graded_ids = {m["id"] for m in spec.get("metrics") or [] if m.get("grader") == "code"}
    for r in pr.get("rows") or []:
        for mid in graded_ids:
            if mid in r and r[mid] is None:
                problems.append(f"{r.get('item_id')}@{r.get('seed')}: {mid} is None (crashed grader)")

    if base_spec is not None:
        for m in base_spec.get("metrics") or []:
            cur = next((x for x in spec.get("metrics") or [] if x["id"] == m["id"]), None)
            if cur is None:
                problems.append(f"ratchet: metric {m['id']} dropped from spec")
                continue
            if m.get("blocking") and not cur.get("blocking"):
                problems.append(f"ratchet: metric {m['id']} is no longer blocking")
            bt, ct = m.get("threshold") or {}, cur.get("threshold") or {}
            if "max" in bt and ("max" not in ct or ct["max"] > bt["max"]):
                problems.append(f"ratchet: {m['id']} max raised {bt.get('max')} -> {ct.get('max')}")
            if "min" in bt and ("min" not in ct or ct["min"] < bt["min"]):
                problems.append(f"ratchet: {m['id']} min lowered {bt.get('min')} -> {ct.get('min')}")
            if bt.get("no_significant_drop") and not ct.get("no_significant_drop"):
                problems.append(f"ratchet: {m['id']} dropped no_significant_drop")
        base_slices = {s["name"]: s for s in base_spec.get("slices") or []}
        cur_slices = {s["name"]: s for s in spec.get("slices") or []}
        for name, s in base_slices.items():
            cs = cur_slices.get(name)
            if cs is None:
                problems.append(f"ratchet: slice {name} dropped from spec")
                continue
            if "min" in s and ("min" not in cs or cs["min"] < s["min"]):
                problems.append(f"ratchet: slice {name} min lowered {s.get('min')} -> {cs.get('min')}")
            if s.get("no_significant_drop") and not cs.get("no_significant_drop"):
                problems.append(f"ratchet: slice {name} dropped no_significant_drop")
            if s.get("blocking") and not cs.get("blocking"):
                problems.append(f"ratchet: slice {name} is no longer blocking")

    base_item_slices = {r["item_id"]: r.get("slices") or [] for r in base.get("rows") or []}
    for r in pr.get("rows") or []:
        want = base_item_slices.get(r["item_id"])
        if want is not None and sorted(r.get("slices") or []) != sorted(want):
            problems.append(f"{r['item_id']}: slice tags {r.get('slices')} differ from baseline's {want}")

    return problems


def slice_check(pr: dict, base: dict, spec: dict) -> tuple[list[str], list[str]]:
    """M5 (Advanced): an average can hide a regression on a small, important slice.
    For each entry of spec["slices"] ({"name", "metric", "min"?, "no_significant_drop"?, "blocking"}):
      - value = mean of per_item(pr, metric, slice_name=name)
      - fail if below "min", or if no_significant_drop and the paired CI over the slice's items
        lies entirely below 0
    Return (blocked ids like "slice:money_movement/pass_rate", report lines)."""
    blocked: list[str] = []
    lines: list[str] = []
    bs = spec.get("bootstrap", {})
    for sl in spec.get("slices") or []:
        name, metric = sl["name"], sl["metric"]
        sid = f"slice:{name}/{metric}"
        a = per_item(pr, metric, slice_name=name)
        if not a:
            lines.append(f"  {sid:<34} no rows in this slice")
            continue
        value = sum(a.values()) / len(a)
        verdict, note = "ok", ""
        if "min" in sl and value < sl["min"]:
            verdict = "fail"
        if sl.get("no_significant_drop"):
            b = per_item(base, metric, slice_name=name)
            keys = sorted(set(a) & set(b))
            if keys:
                d, lo, hi = stats.paired_bootstrap([a[k] for k in keys], [b[k] for k in keys],
                                                   n_resamples=bs.get("n_resamples", 1000), rng=bs.get("rng", 2027))
                note = f"Δ {d:+.3f} CI [{lo:+.3f}, {hi:+.3f}]"
                if hi < 0:
                    verdict = "fail"
        if verdict == "fail" and sl.get("blocking"):
            blocked.append(sid)
        label = "BLOCK" if (verdict == "fail" and sl.get("blocking")) else ("warn" if verdict == "fail" else "ok")
        lines.append(f"  {sid:<34} {value:.4f}   {json.dumps({k: v for k, v in sl.items() if k not in ('name', 'metric')}):<40} {note:<28} {label}")
    return blocked, lines


def check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> tuple[list[str], list[str]]:
    if pr["manifest"]["eval_set_sha"] != base["manifest"]["eval_set_sha"]:
        return ["eval_set_sha"], ["  EVAL SET differs from the baseline's: re-run the baseline on the same eval set"]
    problems = integrity_check(pr, base, spec, base_spec)
    if problems:
        return ["integrity"], [f"  INTEGRITY {p}" for p in problems]
    blocked, lines = [], []
    bs = spec.get("bootstrap", {})
    for m in spec["metrics"]:
        mid, th, val = m["id"], m.get("threshold", {}), pr["metrics"].get(m["id"])
        verdict, note = "ok", ""
        if val is None:
            verdict = "missing"
        elif "max" in th and val > th["max"]:
            verdict = "fail"
        elif "min" in th and val < th["min"]:
            verdict = "fail"
        elif "max_increase" in th and base["metrics"].get(mid):
            if val > base["metrics"][mid] * (1 + th["max_increase"]):
                verdict = "fail"
        if th.get("no_significant_drop") and val is not None:
            a, b = per_item(pr, mid), per_item(base, mid)
            keys = sorted(set(a) & set(b))
            d, lo, hi = stats.paired_bootstrap([a[k] for k in keys], [b[k] for k in keys],
                                               n_resamples=bs.get("n_resamples", 1000), rng=bs.get("rng", 2027))
            note = f"Δ {d:+.3f} CI [{lo:+.3f}, {hi:+.3f}]"
            if hi < 0:
                verdict = "fail"
        if verdict != "ok" and m.get("blocking"):
            blocked.append(mid)
        label = {"ok": "ok", "missing": "MISSING"}.get(verdict, "BLOCK" if m.get("blocking") else "warn")
        lines.append(f"  {mid:<22} {val!s:<8} {json.dumps(th):<40} {note:<28} {label}")
    if spec.get("slices"):
        sb, sl = slice_check(pr, base, spec)
        blocked += sb
        lines += sl
    return blocked, lines


def main(argv: list[str] | None = None) -> int:
    utf8_stdio()
    ap = argparse.ArgumentParser(prog="lab9.gate")
    ap.add_argument("--pr", required=True)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--spec", default=str(SPEC))
    ap.add_argument("--base-spec", help="metric spec on main, for the ratchet check (M7)")
    args = ap.parse_args(argv)
    pr = json.loads(Path(args.pr).read_text(encoding="utf-8"))
    base = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
    base_spec = load_spec(Path(args.base_spec)) if args.base_spec else None
    blocked, lines = check(pr, base, load_spec(Path(args.spec)), base_spec)
    print(f"gate: PR {pr['run_id']} vs main {base['run_id']} · eval set {pr['manifest']['eval_set_sha']}")
    print("\n".join(lines))
    if blocked:
        print(f"exit 1 — blocked: {', '.join(blocked)}")
        return 1
    print("exit 0 — merge")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
