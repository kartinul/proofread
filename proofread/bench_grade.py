import re
from tools import check

def correct(got, want):
    got = re.sub(r"\be\b", "E", re.sub(r"[\\$,]|\\boxed|[{}]", "", got or "")).strip()
    return got == want or check(got, want)[0]
