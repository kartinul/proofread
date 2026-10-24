import ast, subprocess, sys

def auto_print(code):
    # REPL-style: print the last bare expression, since models often forget print()
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return code
    last = tree.body[-1].value if tree.body and isinstance(tree.body[-1], ast.Expr) else None
    if last and not (isinstance(last, ast.Call) and getattr(last.func, "id", "") == "print"):
        tree.body[-1] = ast.Expr(ast.Call(ast.Name("print", ast.Load()), [last], []))
        return ast.unparse(ast.fix_missing_locations(tree))
    return code

def run_sympy(code, timeout=10):
    prog = "from sympy import *\nx, y, z, n, k = symbols('x y z n k')\n" + auto_print(code)
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
