import json
from pathlib import Path

class Memory:
    def __init__(self, path="memory.jsonl"):
        self.path = Path(path)

    def add(self, problem, answer):
        with self.path.open("a") as f:
            f.write(json.dumps({"problem": problem, "answer": answer}) + "\n")

    def recall(self, query, k=3):
        if not self.path.exists():
            return []
        words = set(query.lower().split())
        rows = [json.loads(l) for l in self.path.read_text().splitlines()]
        rows.sort(key=lambda r: -len(words & set(r["problem"].lower().split())))
        return [r for r in rows[:k] if words & set(r["problem"].lower().split())]
