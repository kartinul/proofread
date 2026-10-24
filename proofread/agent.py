import json, os, sys
from openai import OpenAI
from tools import SCHEMAS, run_sympy, check
from memory import Memory

MODEL = os.getenv("MODEL", "qwen3.5:9b-mlx")
client = OpenAI(base_url=os.getenv("BASE_URL", "http://localhost:11434/v1"), api_key=os.getenv("API_KEY", "ollama"), max_retries=8)
SYSTEM = ("You are a math agent. Never trust mental arithmetic: compute with the sympy tool. "
          "Finish by calling `answer` with SymPy `verify` code that prints True. Unverified answers are rejected.")
MAX_CHARS = 12000

def compact(msgs):
    # keep system + problem + last 6 turns; older tool output collapsed to one line
    if sum(len(str(m.get("content") or "")) for m in msgs) < MAX_CHARS:
        return msgs
    head, mid, tail = msgs[:2], msgs[2:-6], msgs[-6:]
    for m in mid:
        if m["role"] == "tool":
            m["content"] = str(m["content"])[:120] + " …[compacted]"
    return head + mid + tail

def solve(problem, mem=Memory(), max_steps=12, log=print):
    msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": problem}]
    seen = set()
    for step in range(max_steps):
        # last 2 steps: force the model to commit instead of looping
        force = {"tool_choice": {"type": "function", "function": {"name": "answer"}}} if step >= max_steps - 2 else {}
        msg = client.chat.completions.create(model=MODEL, messages=compact(msgs), tools=SCHEMAS, **force).choices[0].message
        msgs.append(msg.model_dump(exclude_none=True))
        if not msg.tool_calls:
            msgs.append({"role": "user", "content": "Use tools. Submit via `answer` with verify code."})
            continue
        for call in msg.tool_calls:
            name = call.function.name
            try:
                args = json.loads(call.function.arguments or "{}")
            except json.JSONDecodeError as e:
                args, name = {}, "bad_json"
                out = f"error: tool arguments are not valid JSON ({e}). Retry with valid JSON."
            if name == "bad_json":
                pass
            elif name == "sympy":
                out = run_sympy(args.get("code", ""))
            elif name == "check":
                ok, out = check(args.get("a", ""), args.get("b", ""))
            elif name == "recall":
                out = json.dumps(mem.recall(args.get("query", ""))) or "[]"
            elif name == "answer":
                out = run_sympy(args.get("verify", ""))
                log(f"  answer={args.get('answer')!r} verify→{out}")
                if out.splitlines()[-1:] == ["True"]:
                    mem.add(problem, args["answer"])
                    return args["answer"], True
                out = f"REJECTED: verify printed {out!r}, not True. Fix and resubmit."
            else:
                out = f"unknown tool {name}"
            key = (name, call.function.arguments)
            if key in seen and name != "answer":
                out += "\nLOOP: you already ran this exact call. Stop repeating; call `answer` now."
            seen.add(key)
            log(f"  {name}({json.dumps(args)[:150]}) → {out[:150]}")
            msgs.append({"role": "tool", "tool_call_id": call.id, "content": out})
    return None, False

if __name__ == "__main__":
    print(solve(" ".join(sys.argv[1:]) or input("problem> ")))
