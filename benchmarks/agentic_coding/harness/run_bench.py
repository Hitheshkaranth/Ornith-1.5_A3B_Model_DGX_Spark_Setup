"""Run N opencode agents in parallel (one per task) against one model, then score them with hidden tests.

Example:
  BENCH_API_KEY=sk-... python harness/run_bench.py --label ornith --model-key ornith-1.5-35b-a3b \
      --upstream http://spark-ba51:8080 --parallel 8 --ws-root /tmp/bench_ws
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from proxy import make_server  # noqa: E402

def _find_opencode():
    if os.environ.get("OPENCODE_BIN"):
        return Path(os.environ["OPENCODE_BIN"])
    # on Windows call the native exe directly: the npm .cmd shim mangles multi-line prompts
    win = Path(os.environ.get("APPDATA", "")) / "npm/node_modules/opencode-ai/bin/opencode.exe"
    return win if win.exists() else Path(shutil.which("opencode") or "opencode")


OPENCODE = _find_opencode()

AGENT_MSG = """You are working in the directory {ws}. Complete the programming task below (it is also saved in TASK.md).
Create/modify files in this directory only. Python 3.10 is available as `python` (standard library only; pytest is NOT
installed — use unittest or plain asserts). Test your work before finishing. Stop when the task is complete.

# Task
{prompt}"""


def model_entry(model_key, reasoning=True):
    m = {"name": model_key, "tool_call": True, "reasoning": reasoning, "temperature": True,
         "limit": {"context": 262144, "output": 32768}}
    if reasoning:
        m["interleaved"] = {"field": "reasoning"}
    return m


def free_ram_gb():
    if os.name != "nt":
        return os.sysconf("SC_AVPHYS_PAGES") * os.sysconf("SC_PAGE_SIZE") / 2 ** 30
    import ctypes

    class MS(ctypes.Structure):
        _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong), ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong), ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong), ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong), ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
    m = MS(); m.dwLength = ctypes.sizeof(MS)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    return m.ullAvailPhys / 2 ** 30


def run_agent(task, args, res_dir, port):
    tid = task["id"]
    tdir = ROOT / "tasks" / tid
    ws = Path(args.ws_root) / args.label / tid
    if ws.exists():
        shutil.rmtree(ws)
    shutil.copytree(tdir / "starter", ws)
    prompt = (tdir / "prompt.md").read_text(encoding="utf-8")
    (ws / "TASK.md").write_text(prompt, encoding="utf-8")

    adir = res_dir / "agents" / tid
    adir.mkdir(parents=True, exist_ok=True)
    cfg = {"$schema": "https://opencode.ai/config.json",
           "provider": {"bench": {"npm": "@ai-sdk/openai-compatible", "name": "bench",
                                  "options": {"baseURL": "http://127.0.0.1:%d/%s/v1" % (port, tid), "apiKey": args.api_key},
                                  "models": {args.model_key: model_entry(args.model_key)}}},
           "model": "bench/" + args.model_key}
    cfg_path = adir / "opencode.json"
    cfg_path.write_text(json.dumps(cfg, indent=1))
    # separate opencode data dir per agent: parallel processes sharing one opencode.db hit "database is locked"
    data_home = Path(args.ws_root) / "_data" / args.label / tid
    if data_home.exists():
        shutil.rmtree(data_home)
    (data_home / "opencode").mkdir(parents=True)
    user_data = Path.home() / ".local/share/opencode"
    for f in ("auth.json", "mcp-auth.json"):
        if (user_data / f).exists():
            shutil.copy2(user_data / f, data_home / "opencode" / f)
    env = dict(os.environ, OPENCODE_CONFIG=str(cfg_path), XDG_DATA_HOME=str(data_home))
    cmd = [str(OPENCODE), "run", "--auto", "--format", "json", "--title", "bench-%s-%s" % (args.label, tid),
           "--dir", str(ws), "-m", "bench/" + args.model_key, AGENT_MSG.format(ws=ws, prompt=prompt)]
    t0 = time.time()
    with open(adir / "events.jsonl", "wb") as out, open(adir / "stderr.log", "wb") as err:
        p = subprocess.Popen(cmd, cwd=ws, env=env, stdout=out, stderr=err)
        timed_out = False
        try:
            p.wait(timeout=args.agent_timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            if os.name == "nt":
                subprocess.run(["taskkill", "/T", "/F", "/PID", str(p.pid)], capture_output=True)
            else:
                p.kill()
            p.wait()
    t1 = time.time()
    meta = dict(task=tid, t_start=t0, t_end=t1, wall_s=t1 - t0, exit_code=p.returncode, timed_out=timed_out, ws=str(ws))
    (adir / "meta.json").write_text(json.dumps(meta, indent=1))
    print("[%s] %-28s done in %6.0fs exit=%s%s" % (args.label, tid, t1 - t0, p.returncode, " TIMEOUT" if timed_out else ""), flush=True)
    return meta


def score_agent(tid, ws, adir):
    snap = adir / "final_ws"
    if snap.exists():
        shutil.rmtree(snap)
    shutil.copytree(ws, snap, ignore=shutil.ignore_patterns("__pycache__", ".opencode", "node_modules"))
    test_file = ROOT / "tasks" / tid / "test_hidden.py"
    try:
        r = subprocess.run([sys.executable, str(HERE / "run_hidden.py"), str(snap), str(test_file)],
                           capture_output=True, text=True, timeout=600)
        res = json.loads(r.stdout.strip().splitlines()[-1])
    except Exception as e:
        res = dict(tests=0, passed=0, failed=[], import_error="scoring crashed: %s" % e)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--model-key", required=True)
    ap.add_argument("--upstream", required=True)
    ap.add_argument("--api-key", default=os.environ.get("BENCH_API_KEY", "local"))
    ap.add_argument("--parallel", type=int, default=20)
    ap.add_argument("--port", type=int, default=9100)
    ap.add_argument("--agent-timeout", type=int, default=2700)
    ap.add_argument("--tasks", default="all")
    ap.add_argument("--ws-root", required=True)
    ap.add_argument("--stagger", type=float, default=1.0)
    ap.add_argument("--min-free-gb", type=float, default=2.0)
    args = ap.parse_args()

    manifest = json.loads((ROOT / "tasks" / "manifest.json").read_text())
    if args.tasks != "all":
        want = args.tasks.split(",")
        manifest = [t for t in manifest if any(t["id"].startswith(w) for w in want)]
    res_dir = ROOT / "results" / args.label
    if res_dir.exists():
        shutil.rmtree(res_dir)
    res_dir.mkdir(parents=True)
    srv = make_server(args.port, args.upstream, res_dir / "requests.jsonl")
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    t0 = time.time()
    launch_lock = threading.Lock()

    def launch(it):
        i, t = it
        if i < args.parallel:
            time.sleep(i * args.stagger)
        with launch_lock:  # memory guard: each opencode process needs ~600 MB
            while free_ram_gb() < args.min_free_gb:
                time.sleep(5)
            time.sleep(2)
        return run_agent(t, args, res_dir, args.port)

    with ThreadPoolExecutor(max_workers=args.parallel) as ex:
        metas = list(ex.map(launch, enumerate(manifest)))
    t1 = time.time()
    time.sleep(1)
    srv.shutdown()

    rows = []
    for t, m in zip(manifest, metas):
        s = score_agent(t["id"], Path(m["ws"]), res_dir / "agents" / t["id"])
        total = t["tests"]
        rows.append(dict(task=t["id"], difficulty=t["difficulty"], tests=total, passed=s["passed"],
                         pass_rate=s["passed"] / total, solved=s["passed"] == total, failed=s.get("failed"),
                         import_error=s.get("import_error"), **{k: m[k] for k in ("wall_s", "exit_code", "timed_out")}))
        print("%-28s %2d/%2d %s" % (t["id"], s["passed"], total, s.get("import_error") or ""))
    summary = dict(label=args.label, model=args.model_key, upstream=args.upstream, parallel=args.parallel,
                   run_wall_s=t1 - t0, t_start=t0, t_end=t1, tasks=rows)
    (res_dir / "scores.json").write_text(json.dumps(summary, indent=1))
    print("solved %d/%d, tests %d/%d, wall %.0fs" % (sum(r["solved"] for r in rows), len(rows),
          sum(r["passed"] for r in rows), sum(r["tests"] for r in rows), t1 - t0))


if __name__ == "__main__":
    main()
