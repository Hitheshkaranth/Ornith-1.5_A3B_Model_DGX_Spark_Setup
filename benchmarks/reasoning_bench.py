"""Reasoning + long-output comparison for OpenAI-compatible vLLM servers.

usage: python3 benchmarks/reasoning_bench.py <base_url> <model> <out.json>

  gsm8k      first 100 GSM8K test problems (grade-school math)
  math500    first 100 MATH-500 problems whose answer is an integer
  longform   4 open-ended "write at length" prompts, to see how many tokens
             the model produces before stopping on its own

All requests use the Qwen-recommended thinking-mode sampling
(temperature 0.6, top_p 0.95, top_k 20), 16 in flight, max_tokens 16384
for math and 32768 for longform.
"""

import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

URL, MODEL, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
KEY = os.environ.get("GATEWAY_KEY", "")
CONCURRENCY = 16
SAMPLING = {"temperature": 0.6, "top_p": 0.95, "top_k": 20}
INSTRUCTION = "\n\nPut your final answer as a single number on the last line, in the form: ANSWER: <number>"


def fetch_rows(dataset, config, split, n):
    rows, offset = [], 0
    while len(rows) < n:
        q = urllib.parse.urlencode({"dataset": dataset, "config": config, "split": split,
                                    "offset": offset, "length": 100})
        page = json.load(urllib.request.urlopen(f"https://datasets-server.huggingface.co/rows?{q}"))
        if not page["rows"]:
            break
        rows += [r["row"] for r in page["rows"]]
        offset += 100
    return rows


def load_gsm8k(n=100):
    rows = fetch_rows("openai/gsm8k", "main", "test", n)
    return [(r["question"], r["answer"].split("####")[-1].strip().replace(",", "")) for r in rows[:n]]


def load_math500(n=100):
    out = []
    for r in fetch_rows("HuggingFaceH4/MATH-500", "default", "test", 500):
        a = r["answer"].strip().replace(",", "")
        if re.fullmatch(r"-?\d+", a):
            out.append((r["problem"], a))
        if len(out) == n:
            break
    return out


def chat(prompt, max_tokens):
    body = json.dumps({"model": MODEL, "messages": [{"role": "user", "content": prompt}],
                       "max_tokens": max_tokens, **SAMPLING}).encode()
    headers = {"Content-Type": "application/json"}
    if KEY:
        headers["Authorization"] = f"Bearer {KEY}"
    req = urllib.request.Request(f"{URL}/v1/chat/completions", body, headers)
    t = time.time()
    r = json.load(urllib.request.urlopen(req, timeout=3600))
    c = r["choices"][0]
    return {"content": c["message"].get("content") or "", "finish": c["finish_reason"],
            "tokens": r["usage"]["completion_tokens"], "secs": time.time() - t}


def extract(text):
    m = re.findall(r"ANSWER:\s*\$?(-?[\d,]*\.?\d+)", text)
    if not m:
        m = re.findall(r"\\boxed\{\s*(-?[\d,]*\.?\d+)\s*\}", text) or re.findall(r"-?\d[\d,]*\.?\d*", text)
    if not m:
        return None
    v = m[-1].replace(",", "").rstrip(".")
    try:
        f = float(v)
        return str(int(f)) if f == int(f) else v
    except ValueError:
        return v


def run_math(name, items):
    t = time.time()
    with ThreadPoolExecutor(CONCURRENCY) as ex:
        res = list(ex.map(lambda qa: chat(qa[0] + INSTRUCTION, 16384), items))
    wall = time.time() - t
    correct = [extract(r["content"]) == a for r, (_, a) in zip(res, items)]
    toks = [r["tokens"] for r in res]
    summary = {"n": len(items), "accuracy": sum(correct) / len(items),
               "truncated": sum(r["finish"] == "length" for r in res),
               "avg_tokens": sum(toks) / len(toks), "max_tokens": max(toks),
               "wall_secs": round(wall), "agg_tok_s": round(sum(toks) / wall, 1)}
    print(f"{name:9s} acc={summary['accuracy']:.0%}  avg_tokens={summary['avg_tokens']:.0f}  "
          f"truncated={summary['truncated']}  wall={wall:.0f}s", flush=True)
    return summary


LONG_PROMPTS = [
    "Write a complete, detailed technical guide to building a production-ready REST API in Python, "
    "covering design, auth, database, testing, deployment and monitoring, with full code for each part. "
    "Be as thorough and long as you can.",
    "Write a 10,000-word short story with multiple chapters about a lighthouse keeper who discovers a secret.",
    "Explain the entire history of computing from the abacus to modern AI in as much detail as possible.",
    "Implement a complete chess engine in Python (move generation, all rules, minimax with alpha-beta, "
    "evaluation, UCI interface). Output the full code with no omissions.",
]


def run_longform():
    with ThreadPoolExecutor(len(LONG_PROMPTS)) as ex:
        res = list(ex.map(lambda p: chat(p, 32768), LONG_PROMPTS))
    toks = [r["tokens"] for r in res]
    summary = {"tokens": toks, "avg_tokens": sum(toks) / len(toks), "max_tokens": max(toks),
               "hit_cap": sum(r["finish"] == "length" for r in res)}
    print(f"longform  tokens={toks}  hit_32k_cap={summary['hit_cap']}", flush=True)
    return summary


results = {"model": MODEL}
results["gsm8k"] = run_math("gsm8k", load_gsm8k())
results["math500"] = run_math("math500", load_math500())
results["longform"] = run_longform()
json.dump(results, open(OUT, "w"), indent=2)
