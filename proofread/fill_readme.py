import re, subprocess, sys
table = subprocess.run([sys.executable, "proofread/report.py"], capture_output=True, text=True).stdout.strip()
notes = """
8 hard-for-mental-math problems (big products, roots, integrals, divisor counts, modular powers, Fibonacci, sums of squares, determinants); `bench.py`, graded symbolically. Rows are the problems finished before the hackathon deadline, run through free hosted endpoints of open-weight models.

- **Llama-3.3-70B goes from 0 correct to all correct.** Answering directly, it botches the arithmetic. Under Proofread, every answer is computed and SymPy-verified.
- **gpt-oss-20b** is already strong. The harness keeps it honest: every answer comes with a passing proof.
- **Llama-3.1-8B** shows the limit: it can compute the right value but never commits to an answer. That's what drove the loop-breaker and quirk normalizers above.
- The cost is latency: each answer takes several model calls.
"""
s = open("README.md").read()
s = re.sub(r"## Results\n.*?\n## Run it", "## Results\n\n" + table + "\n" + notes + "\n## Run it", s, flags=re.S)
open("README.md", "w").write(s)
