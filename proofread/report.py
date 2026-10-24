import glob, json

lines = ["| Model | Baseline (answer directly) | Proofread | Verified by SymPy | Avg time base / harness |", "|---|---|---|---|---|"]
for path in sorted(glob.glob("bench_*.json")):
    rows = json.load(open(path))
    n = len(rows)
    score = lambda k: f"{sum(r[k] for r in rows)}/{n}"
    avg = lambda k: sum(r[k] for r in rows) / n
    lines.append(f"| `{path[6:-5]}` | {score('base_ok')} | **{score('harness_ok')}** | {score('verified')} | {avg('t_base'):.0f}s / {avg('t_harness'):.0f}s |")
print("\n".join(lines))
