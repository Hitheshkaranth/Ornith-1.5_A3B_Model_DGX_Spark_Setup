#!/usr/bin/env python3
"""Metering gateway in front of the local vLLM servers.

Every client (Open WebUI, opencode, scripts, LAN users) talks to this
OpenAI-compatible endpoint with its own API key instead of hitting vLLM
directly, so every request is attributed to a user and client and its
token usage is counted.

  - Routing: requests go to whichever vLLM backend serves the requested
    model (backends are polled, so model swaps need no config change).
  - Identity: keys.json maps key -> {user, client}. For a client with
    "forwarded_user": true (Open WebUI), the end user comes from the
    X-OpenWebUI-User-Email header it forwards.
  - Metering: token counts come from vLLM's `usage`. Streaming requests get
    stream_options.include_usage + continuous_usage_stats forced on, so every
    chunk carries running totals and counters update while it streams.
  - Output: Prometheus counters on /metrics, plus one row per request in
    usage.db. Counters are re-seeded from usage.db at startup so totals
    survive restarts.
"""

import asyncio
import json
import os
import sqlite3
import time

import aiohttp
from aiohttp import web
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

HERE = os.path.dirname(os.path.abspath(__file__))
KEYS_PATH = os.environ.get("GATEWAY_KEYS", os.path.join(HERE, "keys.json"))
DB_PATH = os.environ.get("GATEWAY_DB", os.path.join(HERE, "usage.db"))
LISTEN_PORT = int(os.environ.get("GATEWAY_PORT", "8080"))
# 0.0.0.0 = every interface; set to the Tailscale IP to serve the tailnet only.
LISTEN_HOST = os.environ.get("GATEWAY_HOST", "0.0.0.0")
BACKENDS = os.environ.get("GATEWAY_BACKENDS", "http://127.0.0.1:8004").split(",")
POLL_SECONDS = 10
# vLLM runs with --api-key (VLLM_API_KEY); only the gateway holds it, so nothing
# can call vLLM without going through here, even from this host.
UPSTREAM_KEY_PATH = os.environ.get("GATEWAY_UPSTREAM_KEY", os.path.join(HERE, "upstream.key"))
UPSTREAM_KEY = open(UPSTREAM_KEY_PATH).read().strip() if os.path.exists(UPSTREAM_KEY_PATH) else ""
UPSTREAM_HEADERS = {"Authorization": f"Bearer {UPSTREAM_KEY}"} if UPSTREAM_KEY else {}

TOKENS = Counter("llm_user_tokens_total", "Tokens per user, client and model.",
                 ["user", "client", "model", "type"])
REQUESTS = Counter("llm_user_requests_total", "Requests per user, client, model and outcome.",
                   ["user", "client", "model", "status"])
LATENCY = Histogram("llm_request_duration_seconds", "End-to-end request latency through the gateway.",
                    ["client", "model"], buckets=(0.5, 1, 2, 5, 10, 30, 60, 120, 300, 600, 1800))

model_to_backend: dict[str, str] = {}
models_payload: list[dict] = []


# ---------------------------------------------------------------- storage

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS requests (
        ts REAL, user TEXT, client TEXT, model TEXT, path TEXT, status TEXT,
        stream INTEGER, input_tokens INTEGER, output_tokens INTEGER, duration_s REAL)""")
    if "client_ip" not in [r[1] for r in conn.execute("PRAGMA table_info(requests)")]:
        conn.execute("ALTER TABLE requests ADD COLUMN client_ip TEXT")
    return conn


def seed_counters():
    conn = db()
    rows = conn.execute("""SELECT user, client, model, status, COUNT(*),
                           SUM(input_tokens), SUM(output_tokens)
                           FROM requests GROUP BY user, client, model, status""").fetchall()
    for user, client, model, status, n, tin, tout in rows:
        REQUESTS.labels(user, client, model, status).inc(n)
        TOKENS.labels(user, client, model, "input").inc(tin or 0)
        TOKENS.labels(user, client, model, "output").inc(tout or 0)
    conn.close()


def count_live(user, client, model, tin, tout, counted):
    """Add only the not-yet-counted part of running totals to the counters."""
    din, dout = tin - counted[0], tout - counted[1]
    if din > 0:
        TOKENS.labels(user, client, model, "input").inc(din)
        counted[0] = tin
    if dout > 0:
        TOKENS.labels(user, client, model, "output").inc(dout)
        counted[1] = tout


def record(user, client, model, path, status, stream, tin, tout, duration, counted=None, ip=None):
    REQUESTS.labels(user, client, model, status).inc()
    count_live(user, client, model, tin, tout, counted if counted is not None else [0, 0])
    LATENCY.labels(client, model).observe(duration)
    conn = db()
    conn.execute("INSERT INTO requests VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                 (time.time(), user, client, model, path, status, int(stream), tin, tout, duration, ip))
    conn.commit()
    conn.close()


# ---------------------------------------------------------------- routing

async def poll_backends(app):
    session: aiohttp.ClientSession = app["session"]
    while True:
        mapping, payload = {}, []
        for base in BACKENDS:
            try:
                async with session.get(f"{base}/v1/models", headers=UPSTREAM_HEADERS,
                                       timeout=aiohttp.ClientTimeout(total=3)) as r:
                    for m in (await r.json())["data"]:
                        mapping[m["id"]] = base
                        payload.append(m)
            except Exception:
                continue  # backend down (e.g. swapped out); skip it
        model_to_backend.clear()
        model_to_backend.update(mapping)
        models_payload[:] = payload
        await asyncio.sleep(POLL_SECONDS)


def identify(request):
    keys = request.app["keys"]
    auth = request.headers.get("Authorization", "")
    key = auth[7:].strip() if auth.lower().startswith("bearer ") else ""
    entry = keys.get(key)
    if entry is None:
        return None
    user = entry["user"]
    if entry.get("forwarded_user"):
        user = request.headers.get("X-OpenWebUI-User-Email") or f"{entry['client']}:unknown-user"
    return user, entry["client"]


async def count_prompt(session, base, path, payload):
    """Exact prompt size via vLLM /tokenize, so input is counted when a request
    starts rather than when a long (often non-streaming) request finishes."""
    if path.endswith("/chat/completions"):
        body = {k: payload[k] for k in ("model", "messages", "tools", "chat_template_kwargs") if k in payload}
        body["add_generation_prompt"] = True
    elif path.endswith("/completions") and isinstance(payload.get("prompt"), str):
        body = {"model": payload.get("model"), "prompt": payload["prompt"]}
    else:
        return 0
    try:
        async with session.post(f"{base}/tokenize", json=body, headers=UPSTREAM_HEADERS,
                                timeout=aiohttp.ClientTimeout(total=10)) as r:
            return int((await r.json()).get("count", 0)) if r.status == 200 else 0
    except Exception:
        return 0  # fall back to counting from the final usage


# ---------------------------------------------------------------- handlers

async def list_models(request):
    if identify(request) is None:
        return web.json_response({"error": {"message": "invalid API key"}}, status=401)
    return web.json_response({"object": "list", "data": models_payload})


async def proxy(request):
    ident = identify(request)
    if ident is None:
        return web.json_response({"error": {"message": "invalid API key"}}, status=401)
    user, client = ident
    ip = request.remote
    body = await request.read()
    try:
        payload = json.loads(body) if body else {}
    except ValueError:
        return web.json_response({"error": {"message": "invalid JSON"}}, status=400)
    model = payload.get("model", "")
    base = model_to_backend.get(model)
    if base is None:
        record(user, client, model or "none", request.path, "no_backend", False, 0, 0, 0.0, ip=ip)
        return web.json_response({"error": {"message": f"model '{model}' is not being served right now",
                                            "available": sorted(model_to_backend)}}, status=404)

    stream = bool(payload.get("stream"))
    if stream:
        # continuous_usage_stats makes vLLM put running totals on every chunk,
        # so counters move while a long generation is still streaming.
        opts = payload.setdefault("stream_options", {})
        opts["include_usage"] = True
        opts["continuous_usage_stats"] = True
    fwd_headers = {"Content-Type": "application/json", **UPSTREAM_HEADERS}
    started = time.time()
    session: aiohttp.ClientSession = request.app["session"]
    tin = tout = 0
    counted = [0, 0]  # tokens already added to the counters mid-stream
    status = "ok"
    pre = await count_prompt(session, base, request.path, payload)
    if pre:
        count_live(user, client, model, pre, 0, counted)
    try:
        async with session.post(f"{base}{request.path}", json=payload, headers=fwd_headers,
                                timeout=aiohttp.ClientTimeout(total=None, sock_read=1800)) as upstream:
            if not stream or upstream.status != 200:
                data = await upstream.read()
                if upstream.status != 200:
                    status = f"http_{upstream.status}"
                else:
                    usage = (json.loads(data).get("usage") or {})
                    tin, tout = usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)
                return web.Response(body=data, status=upstream.status,
                                    content_type=upstream.content_type)

            resp = web.StreamResponse(status=200, headers={"Content-Type": "text/event-stream",
                                                           "Cache-Control": "no-cache"})
            await resp.prepare(request)
            buf = b""
            async for chunk in upstream.content.iter_any():
                try:
                    await resp.write(chunk)
                except (ConnectionResetError, aiohttp.ClientConnectionResetError):
                    # The client went away mid-stream (e.g. a CLI exiting before a
                    # background request finishes); that's not a vLLM failure.
                    status = "client_disconnect"
                    return resp
                buf += chunk
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    if line.startswith(b"data: {"):
                        try:
                            usage = json.loads(line[6:]).get("usage")
                        except ValueError:
                            usage = None
                        if usage:
                            tin, tout = usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)
                            count_live(user, client, model, tin, tout, counted)
            await resp.write_eof()
            return resp
    except (aiohttp.ClientError, asyncio.TimeoutError, ConnectionResetError) as exc:
        status = "upstream_error"
        return web.json_response({"error": {"message": f"upstream error: {exc}"}}, status=502)
    finally:
        if status != "ok" and not tin:
            tin = counted[0]  # prompt was sent to vLLM even if the request failed
        record(user, client, model, request.path, status, stream, tin, tout, time.time() - started, counted, ip)


async def metrics(_request):
    return web.Response(body=generate_latest(), headers={"Content-Type": CONTENT_TYPE_LATEST})


async def health(_request):
    return web.json_response({"ok": True, "models": sorted(model_to_backend)})


# ---------------------------------------------------------------- app

async def on_startup(app):
    app["session"] = aiohttp.ClientSession()
    app["poller"] = asyncio.create_task(poll_backends(app))


async def on_cleanup(app):
    app["poller"].cancel()
    await app["session"].close()


def main():
    app = web.Application(client_max_size=64 * 1024 * 1024)
    with open(KEYS_PATH) as f:
        app["keys"] = json.load(f)
    seed_counters()
    app.router.add_get("/v1/models", list_models)
    app.router.add_post("/v1/chat/completions", proxy)
    app.router.add_post("/v1/completions", proxy)
    app.router.add_post("/v1/embeddings", proxy)
    app.router.add_get("/metrics", metrics)
    app.router.add_get("/health", health)
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    web.run_app(app, host=LISTEN_HOST, port=LISTEN_PORT, access_log=None)


if __name__ == "__main__":
    main()
