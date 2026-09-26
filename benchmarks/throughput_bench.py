"""Quick decode-throughput check against an OpenAI-compatible vLLM server.

usage: python3 benchmarks/throughput_bench.py <base_url> <model> [concurrency ...]
Each request generates exactly MAX_TOKENS tokens (ignore_eos), so the
numbers compare cleanly across models.
"""

import json
import os
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

MAX_TOKENS = 512
PROMPT = "Write a detailed history of the printing press."
KEY = os.environ.get("GATEWAY_KEY", "")


def one(url, model):
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": PROMPT}],
        "max_tokens": MAX_TOKENS,
        "min_tokens": MAX_TOKENS,
        "ignore_eos": True,
        "temperature": 0.6,
    }).encode()
    headers = {"Content-Type": "application/json"}
    if KEY:
        headers["Authorization"] = f"Bearer {KEY}"
    req = urllib.request.Request(f"{url}/v1/chat/completions", body, headers)
    t = time.time()
    r = json.load(urllib.request.urlopen(req, timeout=600))
    return r["usage"]["completion_tokens"], time.time() - t


def run(url, model, n):
    t = time.time()
    with ThreadPoolExecutor(n) as ex:
        res = list(ex.map(lambda _: one(url, model), range(n)))
    wall = time.time() - t
    toks = sum(r[0] for r in res)
    per_user = sum(r[0] / r[1] for r in res) / n
    print(f"{model:32s} users={n:2d}  aggregate={toks / wall:7.1f} tok/s  "
          f"per-user={per_user:6.1f} tok/s")


url, model = sys.argv[1], sys.argv[2]
levels = [int(x) for x in sys.argv[3:]] or [1, 16]
one(url, model)  # warm-up
for n in levels:
    run(url, model, n)
