# Proofread — a math harness that won't accept unverified answers

Open-weight models are confidently wrong at math. Proofread is a small, open-source **model harness** (≈150 lines of Python) that wraps any OpenAI-compatible model — Ollama, vLLM, OpenRouter, Groq — and enforces one rule:

> **The model proposes. SymPy decides.** A final answer is only accepted if it ships with SymPy code that proves it. Otherwise the harness rejects it, feeds back the failure, and makes the model try again.

## What the harness manages

| Concern | How Proofread handles it | File |
|---|---|---|
| **Prompts** | System prompt forbids mental arithmetic; nudges the model back to tools if it answers in prose | `agent.py` |
| **Tools** | `sympy(code)` — sandboxed subprocess (`python -I`, 10s timeout) with SymPy preloaded · `check(a, b)` — symbolic equality · `recall(query)` — memory search · `answer(answer, verify)` | `tools.py` |
| **Actions / verifier gate** | `answer` runs the model's own `verify` code. Accepted only if it prints `True`. Otherwise: `REJECTED: …` goes back into the loop | `agent.py` |
| **Memory** | Every *verified* answer is appended to `memory.jsonl`; the model can `recall` past results by keyword. Unverified answers never pollute memory | `memory.py` |
| **Context** | When the transcript exceeds a budget, old tool outputs are collapsed to one line, keeping system prompt, the problem and the last 6 turns intact | `agent.py: compact()` |

```
            ┌────────────── REJECTED: verify printed False ─────────────┐
            ▼                                                           │
problem ─► model ──tool call──► sympy / check / recall ──result──► model ──answer+verify──► SymPy runs verify
                                                                                               │ True
                                                                                               ▼
                                                                           accept ─► memory.jsonl
```

## Example

```
$ python agent.py "Find the sum of all real x such that x^3 - 6x^2 + 11x - 6 = 0"
  sympy(solve(x**3-6*x**2+11*x-6)) → [1, 2, 3]  Sum: 6
  answer={"answer":"6","verify":"... sum(symbols) == 6 for symbols in ..."} → REJECTED: SyntaxError
  answer={"answer":"6","verify":"... sum(sol) == 6"}                       → REJECTED: (no output, use print)
  answer='6' verify→True
('6', True)
```

The gate caught two bogus "proofs" before accepting a real one.

## Results

RESULTS_PLACEHOLDER

## Run it

```bash
pip install -r requirements.txt
cd proofread

# local open model via Ollama
MODEL=qwen3.5:9b-mlx python agent.py "How many positive divisors does 7560 have?"

# any OpenAI-compatible endpoint
BASE_URL=https://openrouter.ai/api/v1 API_KEY=... MODEL=meta-llama/llama-3.1-8b-instruct python agent.py "..."

python bench.py        # baseline vs Proofread on the built-in problem set
python test_tools.py   # self-test for tools + memory
```

Env vars: `MODEL`, `BASE_URL` (default `http://localhost:11434/v1`), `API_KEY`.

## Limits

- Verification is only as good as the `verify` code the model writes; a model could write a trivially-true check. The gate catches crashes, wrong arithmetic and missing proofs, not adversarial ones.
- Memory recall is keyword overlap, not embeddings.
- The sandbox is a separate isolated Python process with a timeout, not a container — run untrusted models in a VM.

## License

MIT
