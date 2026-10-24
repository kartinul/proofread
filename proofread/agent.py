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

def text_call(content):
    # open models often print a tool call as JSON text instead of using the tool API
    try:
        args = json.loads(content[content.index("{"):content.rindex("}") + 1])
    except ValueError:
        return None
    if not isinstance(args, dict):
        return None
    name = args.pop("name", None) or ("answer" if "verify" in args else "sympy" if "code" in args else "check" if "a" in args else None)
    args = args.get("arguments", args)
    return (name, args) if name else None

def unwrap(args):
    while len(args) == 1 and isinstance(next(iter(args.values())), dict):
        args = next(iter(args.values()))
    return args

def run_tool(name, args, problem, mem, log):
    args = unwrap(args)
    if name == "sympy":
        return run_sympy(args.get("code", "")), None
    if name == "check":
        return check(args.get("a", ""), args.get("b", ""))[1], None
    if name == "recall":
        return json.dumps(mem.recall(args.get("query", ""))), None
    if name == "answer":
        out = run_sympy(args.get("verify", ""))
        log(f"  answer={args.get('answer')!r} verify→{out}")
        if out.splitlines()[-1:] == ["True"]:
            mem.add(problem, str(args["answer"]))
            return out, str(args["answer"])
        return f"REJECTED: verify printed {out!r}, not True. Fix and resubmit.", None
    return f"unknown tool {name}", None

def solve(problem, mem=Memory(), max_steps=12, log=print):
    msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": problem}]
    seen = set()
    for step in range(max_steps):
        # last 2 steps: force the model to commit instead of looping
        force = {"tool_choice": {"type": "function", "function": {"name": "answer"}}} if step >= max_steps - 2 else {}
        msg = client.chat.completions.create(model=MODEL, messages=compact(msgs), tools=SCHEMAS, **force).choices[0].message
        msgs.append(msg.model_dump(exclude_none=True))
        calls = []
        for call in msg.tool_calls or []:
            try:
                args = json.loads(call.function.arguments or "{}")
                assert isinstance(args, dict)
                calls.append((call.id, call.function.name, args))
            except (json.JSONDecodeError, AssertionError) as e:
                msgs.append({"role": "tool", "tool_call_id": call.id, "content": f"error: arguments are not valid JSON ({e}). Retry."})
        if not msg.tool_calls:
            parsed = text_call(msg.content or "")
            if not parsed:
                log(f"  prose: {(msg.content or '')[:150]!r}")
                msgs.append({"role": "user", "content": "Do not answer in prose. Call the `answer` tool with `answer` and SymPy `verify` code that prints True."})
                continue
            calls.append((None, *parsed))
        for call_id, name, args in calls:
            out, final = run_tool(name, args, problem, mem, log)
            if final is not None:
                return final, True
            key = (name, json.dumps(args, sort_keys=True))
            if key in seen and name != "answer":
                out += "\nLOOP: you already ran this exact call. Stop repeating; call `answer` now."
            seen.add(key)
            log(f"  {name}({json.dumps(args)[:150]}) → {out[:150]}")
            msgs.append({"role": "tool", "tool_call_id": call_id, "content": out} if call_id else {"role": "user", "content": f"[{name} result] {out}"})
    return None, False

if __name__ == "__main__":
    print(solve(" ".join(sys.argv[1:]) or input("problem> ")))
