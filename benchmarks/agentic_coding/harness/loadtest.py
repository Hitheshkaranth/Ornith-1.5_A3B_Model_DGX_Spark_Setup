"""Server load test: TTFT and decode speed at 1 / 8 / 20 concurrent streams with agent-sized prompts.

Each request carries ~40k tokens of context (like an opencode agent turn) and is forced to generate exactly
OUT tokens (min_tokens = max_tokens), so decode rates are comparable.
  warm : all requests share the 40k prefix (prefix cache hits - what agents mostly see)
  cold : every request has a unique prefix (full prefill)

usage: python harness/loadtest.py <label> <upstream> <model> <api_key>
"""
import glob
import http.client
import json
import os
import random
import statistics as st
import sys
import threading
import time
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = 512


def context_text(chars=150_000):
    lib = os.path.dirname(os.__file__)
    buf = []
    for f in sorted(glob.glob(os.path.join(lib, "*.py"))):
        buf.append(open(f, encoding="utf-8", errors="replace").read())
        if sum(map(len, buf)) > chars:
            break
    return "".join(buf)[:chars]


def one(up, model, key, prompt, res):
    body = json.dumps({"model": model, "stream": True, "stream_options": {"include_usage": True},
                       "max_tokens": OUT, "min_tokens": OUT, "temperature": 0.6,
                       "messages": [{"role": "system", "content": prompt},
                                    {"role": "user", "content": "Summarise what the code above does, module by module."}]})
    conn = http.client.HTTPConnection(up.hostname, up.port, timeout=1800)
    t0 = time.time(); t_first = None; usage = None; buf = b""
    conn.request("POST", "/v1/chat/completions", body=body,
                 headers={"Content-Type": "application/json", "Authorization": "Bearer " + key})
    r = conn.getresponse()
    while True:
        ch = r.read1(65536)
        if not ch:
            break
        buf += ch
        while b"\n" in buf:
            line, buf = buf.split(b"\n", 1)
            line = line.strip()
            if not line.startswith(b"data:") or line[5:].strip() == b"[DONE]":
                continue
            ev = json.loads(line[5:])
            if ev.get("usage"):
                usage = ev["usage"]
            for c in ev.get("choices") or []:
                d = c.get("delta") or {}
                if t_first is None and (d.get("content") or d.get("reasoning_content") or d.get("reasoning")):
                    t_first = time.time()
    t1 = time.time()
    n = (usage or {}).get("completion_tokens", 0)
    res.append(dict(status=r.status, ttft=(t_first - t0) if t_first else None, total=t1 - t0, completion=n,
                    prompt=(usage or {}).get("prompt_tokens"), rate=(n - 1) / (t1 - t_first) if t_first and n > 1 else None))


def scenario(up, model, key, conc, warm, ctx):
    res, ths = [], []
    for i in range(conc):
        nonce = "" if warm else "Session %d-%d.\n" % (random.randrange(10**9), i)
        prompt = nonce + ctx + ("\n# request %d\n" % i)
        ths.append(threading.Thread(target=one, args=(up, model, key, prompt, res)))
    t0 = time.time()
    for t in ths: t.start()
    for t in ths: t.join()
    wall = time.time() - t0
    ttft = [r["ttft"] for r in res if r["ttft"] is not None]
    rate = [r["rate"] for r in res if r["rate"] is not None]
    out = dict(concurrency=conc, cache="warm" if warm else "cold", n=len(res), errors=sum(r["status"] != 200 for r in res),
               prompt_tokens=res[0]["prompt"], ttft_p50=st.median(ttft), ttft_max=max(ttft), ttft_min=min(ttft),
               per_stream_tok_s_p50=st.median(rate), per_stream_tok_s_min=min(rate),
               aggregate_tok_s=sum(r["completion"] for r in res) / wall, wall_s=wall, raw=res)
    print("%-4s conc=%2d  TTFT p50 %.2fs max %.2fs | per-stream %.1f tok/s | aggregate %.0f tok/s" % (
        out["cache"], conc, out["ttft_p50"], out["ttft_max"], out["per_stream_tok_s_p50"], out["aggregate_tok_s"]), flush=True)
    return out


def main():
    label, upstream, model, key = sys.argv[1:5]
    up = urlparse(upstream)
    ctx = context_text()
    scenario(up, model, key, 1, True, ctx)  # prime the prefix cache
    results = [scenario(up, model, key, c, True, ctx) for c in (1, 8, 20)]
    results += [scenario(up, model, key, c, False, ctx) for c in (1, 20)]
    os.makedirs(os.path.join(ROOT, "results", label), exist_ok=True)
    with open(os.path.join(ROOT, "results", label, "loadtest.json"), "w") as f:
        json.dump(results, f, indent=1)


if __name__ == "__main__":
    main()
