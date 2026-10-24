import os, tempfile
from tools import run_sympy, check
from memory import Memory

assert run_sympy("print(factor(x**2-1))".replace("x", "Symbol('x')")) == "(x - 1)*(x + 1)"
assert check("sin(x)**2 + cos(x)**2", "1")[0]
assert not check("x + 1", "x")[0]
assert run_sympy("while True: pass", timeout=1) == "error: timeout"
m = Memory(os.path.join(tempfile.mkdtemp(), "m.jsonl"))
m.add("sum of roots of cubic", "6")
assert m.recall("roots cubic")[0]["answer"] == "6" and m.recall("zebra") == []
print("ok")
