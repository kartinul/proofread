import json, subprocess, sys

def run_sympy(code, timeout=10):
    prog = "from sympy import *\n" + code
    try:
        r = subprocess.run([sys.executable, "-I", "-c", prog], capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return "error: timeout"
    return (r.stdout + r.stderr).strip()[-2000:] or "(no output, use print)"

def check(a, b):
    out = run_sympy(f"print(simplify(sympify({a!r}) - sympify({b!r})) == 0)")
    return out == "True", out

SCHEMAS = [
    {"type": "function", "function": {"name": "sympy", "description": "Run Python with `from sympy import *` preloaded. Print results.",
        "parameters": {"type": "object", "properties": {"code": {"type": "string"}}, "required": ["code"]}}},
    {"type": "function", "function": {"name": "check", "description": "Verify two expressions are symbolically equal.",
        "parameters": {"type": "object", "properties": {"a": {"type": "string"}, "b": {"type": "string"}}, "required": ["a", "b"]}}},
    {"type": "function", "function": {"name": "recall", "description": "Search memory of previously verified results.",
        "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "answer", "description": "Submit final answer. `verify` is SymPy code that prints True iff the answer is correct (e.g. substitute back).",
        "parameters": {"type": "object", "properties": {"answer": {"type": "string"}, "verify": {"type": "string"}}, "required": ["answer", "verify"]}}},
]
