import json, re, time
from agent import client, MODEL, solve
from memory import Memory
from tools import check

PROBLEMS = [
    ("What is 7919 * 4231?", "33505289"),
    ("Sum of all real roots of x^3 - 6x^2 + 11x - 6 = 0?", "6"),
    ("Compute the integral of x^2 * e^x from 0 to 1. Give exact form.", "E - 2"),
    ("How many positive divisors does 7560 have?", "64"),
    ("What is the remainder when 3^200 is divided by 13?", "9"),
    ("Find the 30th Fibonacci number (F1=F2=1).", "832040"),
    ("Sum of the squares of the first 123 positive integers?", "627874"),
    ("Determinant of [[2,3,1],[4,1,5],[7,2,9]]?", "-4"),
]

def baseline(q):
    r = client.chat.completions.create(model=MODEL, messages=[{"role": "user", "content": q + " Reply with only the final answer."}])
    return (r.choices[0].message.content or "").strip().splitlines()[-1]

def correct(got, want):
    got = re.sub(r"[\\$,]|\\boxed|[{}]", "", got or "").strip()
    return got == want or check(got, want)[0]

rows = []
for q, want in PROBLEMS:
    t = time.time(); b = baseline(q); tb = time.time() - t
    t = time.time()
    try:
        h, verified = solve(q, Memory(f"/tmp/pr_{MODEL}.jsonl"), log=lambda *a: None)
    except Exception as e:
        h, verified = None, False
        print("solve error:", e, flush=True)
    th = time.time() - t
    rows.append({"q": q, "want": want, "baseline": b, "base_ok": correct(b, want), "harness": h, "harness_ok": correct(h, want),
                 "verified": verified, "t_base": round(tb, 1), "t_harness": round(th, 1)})
    print(json.dumps(rows[-1]), flush=True)

n = len(rows)
print(f"\nbaseline {sum(r['base_ok'] for r in rows)}/{n} | proofread {sum(r['harness_ok'] for r in rows)}/{n}")
json.dump(rows, open(f"bench_{MODEL.replace('/','_')}.json", "w"), indent=1)
