"""MMLU-Pro knowledge benchmark for OpenAI-compatible vLLM servers.

usage: GATEWAY_KEY=sk-... uv run --no-project --with pyarrow \
         python3 benchmarks/knowledge_bench.py <base_url> <model> <out.json> [per_category]

MMLU-Pro (TIGER-Lab, NeurIPS 2024) is the harder successor to MMLU: 12,032
expert-level questions across 14 subjects, 10 options each (A-J), so random
guessing scores 10% instead of MMLU's 25%.

This runs a stratified sample: `per_category` questions (default 50) drawn with a
fixed seed from each of the 14 categories, 700 in total. Zero-shot, thinking on,
Qwen-recommended sampling (temperature 0.6, top_p 0.95, top_k 20), max_tokens 16384,
8 requests in flight so a live server still has room for real users.

Per-question records are appended to <out>.jsonl as they finish, so an interrupted
run resumes where it stopped.
"""

import json
import os
import random
import re
import sys
import time
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

URL, MODEL, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
PER_CATEGORY = int(sys.argv[4]) if len(sys.argv) > 4 else 50
KEY = os.environ.get("GATEWAY_KEY", "")
CONCURRENCY = 8
MAX_TOKENS = 16384
SEED = 0
SAMPLING = {"temperature": 0.6, "top_p": 0.95, "top_k": 20}
LETTERS = "ABCDEFGHIJ"
INSTRUCTION = ("Answer the following multiple choice question. Think step by step, then put your "
               "final answer on the last line in the form: ANSWER: <letter>")


PARQUET = ("https://huggingface.co/datasets/TIGER-Lab/MMLU-Pro/resolve/main/"
           "data/test-00000-of-00001.parquet")
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache", "mmlu_pro_test.parquet")


def fetch_all():
    # One official parquet file; the datasets-server rows API rate-limits (429) long before 12k rows.
    import pyarrow.parquet as pq
    if not os.path.exists(CACHE):
        os.makedirs(os.path.dirname(CACHE), exist_ok=True)
        urllib.request.urlretrieve(PARQUET, CACHE + ".part")
        os.replace(CACHE + ".part", CACHE)
    return pq.read_table(CACHE).to_pylist()


def load_sample():
    by_cat = defaultdict(list)
    for r in fetch_all():
        by_cat[r["category"]].append(r)
    rng = random.Random(SEED)
    sample = []
    for cat in sorted(by_cat):
        rows = sorted(by_cat[cat], key=lambda r: r["question_id"])
        sample += rng.sample(rows, min(PER_CATEGORY, len(rows)))
    return sample


def prompt(row):
    opts = "\n".join(f"{LETTERS[i]}. {o}" for i, o in enumerate(row["options"]))
    return f"{INSTRUCTION}\n\nQuestion: {row['question']}\n\nOptions:\n{opts}"


def chat(text):
    body = json.dumps({"model": MODEL, "messages": [{"role": "user", "content": text}],
                       "max_tokens": MAX_TOKENS, **SAMPLING}).encode()
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
    m = re.findall(r"ANSWER:\s*\**\(?([A-J])\b", text)
    if not m:
        m = re.findall(r"answer is:?\s*\**\(?([A-J])\b", text, re.I)
    if not m:
        m = re.findall(r"\\boxed\{\s*(?:\\text\{)?([A-J])\b", text)
    return m[-1] if m else None


def run_one(row):
    for attempt in range(3):
        try:
            r = chat(prompt(row))
            break
        except Exception as e:
            if attempt == 2:
                r = {"content": "", "finish": f"error: {e}", "tokens": 0, "secs": 0}
            time.sleep(5)
    pred = extract(r["content"])
    return {"question_id": row["question_id"], "category": row["category"], "answer": row["answer"],
            "pred": pred, "correct": pred == row["answer"], "finish": r["finish"],
            "tokens": r["tokens"], "secs": round(r["secs"], 1)}


def main():
    sample = load_sample()
    log = OUT.rsplit(".json", 1)[0] + ".jsonl"
    done = {}
    if os.path.exists(log):
        for line in open(log):
            rec = json.loads(line)
            if not str(rec["finish"]).startswith("error"):
                done[rec["question_id"]] = rec
    todo = [r for r in sample if r["question_id"] not in done]
    print(f"MMLU-Pro: {len(sample)} questions, {len(done)} already done, {len(todo)} to run", flush=True)

    t0 = time.time()
    with open(log, "a") as f, ThreadPoolExecutor(CONCURRENCY) as ex:
        for i, rec in enumerate(ex.map(run_one, todo), 1):
            done[rec["question_id"]] = rec
            f.write(json.dumps(rec) + "\n")
            f.flush()
            if i % 25 == 0 or i == len(todo):
                acc = sum(r["correct"] for r in done.values()) / len(done)
                print(f"  {i}/{len(todo)}  running acc {acc:.3f}  {time.time() - t0:.0f}s", flush=True)
    wall = time.time() - t0

    recs = [done[r["question_id"]] for r in sample]
    cats = defaultdict(list)
    for r in recs:
        cats[r["category"]].append(r)
    result = {
        "model": MODEL,
        "benchmark": "MMLU-Pro (TIGER-Lab/MMLU-Pro, test split)",
        "method": (f"stratified sample, {PER_CATEGORY}/category x {len(cats)} categories, seed {SEED}; "
                   f"zero-shot, thinking on, temperature 0.6 / top_p 0.95 / top_k 20, "
                   f"max_tokens {MAX_TOKENS}, {CONCURRENCY} in flight"),
        "n": len(recs),
        "accuracy": round(sum(r["correct"] for r in recs) / len(recs), 4),
        "unparsed": sum(r["pred"] is None for r in recs),
        "truncated": sum(r["finish"] == "length" for r in recs),
        "avg_tokens": round(sum(r["tokens"] for r in recs) / len(recs), 1),
        "wall_secs_this_run": round(wall),
        "by_category": {c: {"n": len(v), "accuracy": round(sum(r["correct"] for r in v) / len(v), 3)}
                        for c, v in sorted(cats.items())},
    }
    json.dump(result, open(OUT, "w"), indent=2)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
