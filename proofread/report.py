import glob, json, os

lines = ["| Model | Baseline (answer directly) | Proofread | Verified by SymPy | Avg time base / harness |", "|---|---|---|---|---|"]
for path in sorted(glob.glob(os.path.join(os.path.dirname(__file__), "..", "bench_*.log"))):
    rows = [json.loads(l) for l in open(path) if l.startswith("{")]
    if not rows:
        continue
    n = len(rows)
    score = lambda k: f"{sum(r[k] for r in rows)}/{n}"
    avg = lambda k: sum(r[k] for r in rows) / n
    lines.append(f"| `{os.path.basename(path)[6:-4]}` | {score('base_ok')} | **{score('harness_ok')}** | {score('verified')} | {avg('t_base'):.0f}s / {avg('t_harness'):.0f}s |")
print("\n".join(lines))
