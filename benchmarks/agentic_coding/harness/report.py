"""Aggregate scores + proxy logs into metrics (TTFT, token rate, token totals) and plot them.

usage: python harness/report.py ornith [qwen ...]
Writes results/summary.json, results/per_task.csv, results/benchmark.png
"""
import csv
import json
import statistics as st
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "results"

# reference palette (light surface) - categorical slots in fixed order
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e6e5e0"


def pct(xs, p):
    xs = sorted(xs)
    if not xs:
        return float("nan")
    k = (len(xs) - 1) * p / 100
    f = int(k)
    return xs[f] + (xs[min(f + 1, len(xs) - 1)] - xs[f]) * (k - f)


def load(label):
    scores = json.loads((RES / label / "scores.json").read_text())
    reqs = [json.loads(l) for l in open(RES / label / "requests.jsonl", encoding="utf-8")]
    chat = [r for r in reqs if r["path"].endswith("/chat/completions")]
    t0 = scores["t_start"]
    out = []
    for r in chat:
        u = r.get("usage") or {}
        d = dict(tag=r["tag"], ok=r.get("status") == 200 and not r.get("error"), t_req=r["t_req"] - t0, t_end=r["t_end"] - t0,
                 prompt=u.get("prompt_tokens") or 0, completion=u.get("completion_tokens") or 0,
                 cached=(u.get("prompt_tokens_details") or {}).get("cached_tokens"), ttft=None, rate=None, finish=r.get("finish"))
        if r.get("t_first"):
            d["ttft"] = r["t_first"] - r["t_req"]
            gen = r["t_end"] - r["t_first"]
            if gen > 0.5 and d["completion"] >= 16:
                d["rate"] = (d["completion"] - 1) / gen
        out.append(d)
    # in-flight concurrency at each request's start
    ev = sorted([(x["t_req"], 1) for x in out] + [(x["t_end"], -1) for x in out])
    for x in out:
        x["inflight"] = sum(1 for y in out if y["t_req"] <= x["t_req"] < y["t_end"])
    return scores, out, ev


def summarize(label, scores, reqs):
    ok = [r for r in reqs if r["ok"]]
    ttft = [r["ttft"] for r in ok if r["ttft"] is not None]
    rate = [r["rate"] for r in ok if r["rate"] is not None]
    span = max(r["t_end"] for r in ok) - min(r["t_req"] for r in ok)
    comp = sum(r["completion"] for r in ok)
    prompt = sum(r["prompt"] for r in ok)
    cached = [r["cached"] for r in ok if r["cached"] is not None]
    tasks = scores["tasks"]
    per_task = []
    for t in tasks:
        rr = [r for r in ok if r["tag"] == t["task"]]
        tt = [r["ttft"] for r in rr if r["ttft"] is not None]
        ra = [r["rate"] for r in rr if r["rate"] is not None]
        per_task.append(dict(model=label, task=t["task"], difficulty=t["difficulty"], passed=t["passed"], tests=t["tests"],
                             solved=t["solved"], wall_s=round(t["wall_s"], 1), timed_out=t["timed_out"], requests=len(rr),
                             prompt_tokens=sum(r["prompt"] for r in rr), completion_tokens=sum(r["completion"] for r in rr),
                             total_tokens=sum(r["prompt"] + r["completion"] for r in rr),
                             ttft_median_s=round(st.median(tt), 3) if tt else None,
                             ttft_p90_s=round(pct(tt, 90), 3) if tt else None,
                             decode_tok_s_median=round(st.median(ra), 1) if ra else None))
    s = dict(model=label, upstream=scores["upstream"], parallel_agents=scores["parallel"],
             solved=sum(t["solved"] for t in tasks), n_tasks=len(tasks),
             tests_passed=sum(t["passed"] for t in tasks), tests_total=sum(t["tests"] for t in tasks),
             mean_pass_rate=st.mean(t["pass_rate"] for t in tasks),
             run_wall_s=scores["run_wall_s"], requests=len(reqs), failed_requests=len(reqs) - len(ok),
             ttft_s=dict(mean=st.mean(ttft), p50=pct(ttft, 50), p90=pct(ttft, 90), p99=pct(ttft, 99), max=max(ttft)),
             decode_tok_s_per_stream=dict(mean=st.mean(rate), p10=pct(rate, 10), p50=pct(rate, 50), p90=pct(rate, 90)),
             aggregate_output_tok_s=comp / span,
             prompt_tokens=prompt, completion_tokens=comp, total_tokens=prompt + comp,
             cached_prompt_tokens=sum(cached) if cached else None,
             peak_inflight=max(r["inflight"] for r in reqs))
    return s, per_task


def style(ax, title):
    ax.set_facecolor(SURFACE)
    ax.set_title(title, loc="left", fontsize=11, color=INK, fontweight="bold", pad=8)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    for sp in ("left", "bottom"):
        ax.spines[sp].set_color(GRID)
    ax.tick_params(colors=INK2, labelsize=8, length=0)
    ax.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def plot(data, path):
    labels = list(data)
    n = len(labels)
    has_lt = any(data[lb].get("loadtest") for lb in labels)
    fig, axs = plt.subplots(4 if has_lt else 3, 2, figsize=(15, 20.5 if has_lt else 15.5), facecolor=SURFACE,
                            gridspec_kw=dict(hspace=0.42, wspace=0.28))
    tasks = [t["task"] for t in data[labels[0]]["per_task"]]
    y = list(range(len(tasks)))
    h = 0.8 / n

    # (a) hidden-test pass rate per task
    ax = axs[0, 0]; style(ax, "Hidden tests passed per task")
    for i, lb in enumerate(labels):
        pt = {r["task"]: r for r in data[lb]["per_task"]}
        vals = [100 * pt[t]["passed"] / pt[t]["tests"] for t in tasks]
        ys = [v + (i - (n - 1) / 2) * h for v in y]
        ax.barh(ys, vals, height=h * 0.85, color=SERIES[i], label=lb, edgecolor=SURFACE, linewidth=1)
        for yy, t in zip(ys, tasks):
            r = pt[t]
            ax.text(min(100 * r["passed"] / r["tests"], 100) + 1.5, yy, "%d/%d" % (r["passed"], r["tests"]), va="center", fontsize=7, color=INK2)
    ax.set_yticks(y); ax.set_yticklabels(tasks, fontsize=8, color=INK); ax.invert_yaxis(); ax.set_xlim(0, 112)
    ax.set_xlabel("% of hidden tests passed", color=INK2, fontsize=9); ax.grid(axis="y", visible=False)

    # (b) tokens consumed per task (output tokens; prompt totals in summary)
    ax = axs[0, 1]; style(ax, "Output tokens generated per task (incl. reasoning)")
    for i, lb in enumerate(labels):
        pt = {r["task"]: r for r in data[lb]["per_task"]}
        vals = [pt[t]["completion_tokens"] / 1000 for t in tasks]
        ys = [v + (i - (n - 1) / 2) * h for v in y]
        ax.barh(ys, vals, height=h * 0.85, color=SERIES[i], label=lb, edgecolor=SURFACE, linewidth=1)
        for yy, t, v in zip(ys, tasks, vals):
            ax.text(v, yy, "  %.1fk · %d req" % (v, pt[t]["requests"]), va="center", fontsize=7, color=INK2)
    ax.set_yticks(y); ax.set_yticklabels(tasks, fontsize=8, color=INK); ax.invert_yaxis()
    ax.set_xlabel("thousand output tokens", color=INK2, fontsize=9); ax.grid(axis="y", visible=False)
    ax.set_xlim(0, ax.get_xlim()[1] * 1.25)

    # (c) TTFT per request across the run
    ax = axs[1, 0]; style(ax, "Time to first token, every agent request")
    for i, lb in enumerate(labels):
        rq = [r for r in data[lb]["reqs"] if r["ok"] and r["ttft"] is not None]
        ax.scatter([r["t_req"] / 60 for r in rq], [r["ttft"] for r in rq], s=10, color=SERIES[i], alpha=0.55, linewidths=0, label=lb)
        s = data[lb]["summary"]["ttft_s"]
        ax.axhline(s["p50"], color=SERIES[i], linewidth=1, linestyle="--")
        ax.text(ax.get_xlim()[1] if False else 0.2, s["p50"], " p50 %.2fs" % s["p50"], color=INK2, fontsize=8, va="bottom")
    ax.set_ylim(0, None); ax.set_xlabel("minutes since run start", color=INK2, fontsize=9); ax.set_ylabel("TTFT (s)", color=INK2, fontsize=9)

    # (d) in-flight requests over time
    ax = axs[1, 1]; style(ax, "Concurrent in-flight requests at the server")
    for i, lb in enumerate(labels):
        ev = data[lb]["ev"]; cur = 0; xs, ys = [], []
        for t, d in ev:
            xs.append(t / 60); ys.append(cur); cur += d; xs.append(t / 60); ys.append(cur)
        ax.plot(xs, ys, color=SERIES[i], linewidth=1.5, label=lb)
    ax.set_xlabel("minutes since run start", color=INK2, fontsize=9); ax.set_ylabel("requests in flight", color=INK2, fontsize=9)

    # (e) decode speed vs concurrency
    ax = axs[2, 0]; style(ax, "Per-stream decode speed vs. concurrent load")
    for i, lb in enumerate(labels):
        rq = [r for r in data[lb]["reqs"] if r["ok"] and r["rate"] is not None]
        ax.scatter([r["inflight"] for r in rq], [r["rate"] for r in rq], s=10, color=SERIES[i], alpha=0.5, linewidths=0, label=lb)
    ax.set_xlabel("requests in flight when the request started", color=INK2, fontsize=9); ax.set_ylabel("output tok/s (single stream)", color=INK2, fontsize=9)

    # (f) summary table
    ax = axs[2, 1]; ax.axis("off"); ax.set_title("Summary", loc="left", fontsize=11, color=INK, fontweight="bold", pad=8)
    rows = [("Tasks fully solved", lambda s: "%d / %d" % (s["solved"], s["n_tasks"])),
            ("Hidden tests passed", lambda s: "%d / %d (%.1f%%)" % (s["tests_passed"], s["tests_total"], 100 * s["tests_passed"] / s["tests_total"])),
            ("Run wall time", lambda s: "%.1f min" % (s["run_wall_s"] / 60)),
            ("LLM requests", lambda s: "%d" % s["requests"]),
            ("TTFT p50 / p90 / p99", lambda s: "%.2f / %.2f / %.2f s" % (s["ttft_s"]["p50"], s["ttft_s"]["p90"], s["ttft_s"]["p99"])),
            ("Decode tok/s per stream (p50)", lambda s: "%.1f" % s["decode_tok_s_per_stream"]["p50"]),
            ("Aggregate output tok/s", lambda s: "%.0f" % s["aggregate_output_tok_s"]),
            ("Prompt tokens", lambda s: "%.2f M" % (s["prompt_tokens"] / 1e6)),
            ("Output tokens", lambda s: "%.0f k" % (s["completion_tokens"] / 1e3)),
            ("Total tokens", lambda s: "%.2f M" % (s["total_tokens"] / 1e6)),
            ("Peak in-flight requests", lambda s: "%d" % s["peak_inflight"])]
    cell = [[name] + [f(data[lb]["summary"]) for lb in labels] for name, f in rows]
    tb = ax.table(cellText=cell, colLabels=["Metric"] + labels, loc="upper left", cellLoc="left", colLoc="left",
                  colWidths=[0.48] + [0.52 / n] * n)
    tb.auto_set_font_size(False); tb.set_fontsize(9.5); tb.scale(1, 1.75)
    for (r, c), cl in tb.get_celld().items():
        cl.set_edgecolor(GRID); cl.set_facecolor(SURFACE); cl.get_text().set_color(INK if c else INK2)
        if r == 0:
            cl.get_text().set_fontweight("bold")

    if has_lt:
        scen = [(1, "warm"), (8, "warm"), (20, "warm"), (1, "cold"), (20, "cold")]
        names = ["%d stream%s / %s cache" % (c, "s" if c > 1 else "", k) for c, k in scen]
        names = [nm.replace(" / ", "\n") for nm in names]
        x = list(range(len(scen)))
        for row, (key, title, ylab, fmt) in enumerate([
                ("ttft_p50", "Load test: median TTFT, ~40k-token prompt", "TTFT p50 (s)", "%.2fs"),
                ("per_stream_tok_s_p50", "Load test: decode speed per stream (512 forced output tokens)", "output tok/s per stream", "%.0f")]):
            ax = axs[3, row]; style(ax, title)
            for i, lb in enumerate(labels):
                lt = {(r["concurrency"], r["cache"]): r for r in data[lb].get("loadtest") or []}
                vals = [lt[k][key] if k in lt else 0 for k in scen]
                xs = [v + (i - (n - 1) / 2) * h for v in x]
                ax.bar(xs, vals, width=h * 0.85, color=SERIES[i], label=lb, edgecolor=SURFACE, linewidth=1)
                for xx, k, v in zip(xs, scen, vals):
                    lab = fmt % v
                    if key == "per_stream_tok_s_p50" and k in lt:
                        lab += "\n(%.0f total)" % lt[k]["aggregate_tok_s"]
                    ax.text(xx, v, lab, ha="center", va="bottom", fontsize=7.5, color=INK2)
            ax.set_xticks(x); ax.set_xticklabels(names, fontsize=8, color=INK); ax.grid(axis="x", visible=False)
            ax.set_ylabel(ylab, color=INK2, fontsize=9); ax.set_ylim(0, ax.get_ylim()[1] * 1.18)

    if n > 1:
        axs[0, 0].legend(frameon=False, fontsize=9, loc="lower right")
    model_names = " vs ".join(labels)
    fig.suptitle("opencode agent benchmark: %s · 20 coding tasks, one opencode agent each" % model_names,
                 x=0.06, ha="left", fontsize=14, color=INK, fontweight="bold", y=0.985)
    fig.text(0.06, 0.968, "vLLM on spark-ba51 · TTFT = request sent -> first streamed token (reasoning, text or tool call), measured "
             "at a local proxy, so it includes queueing + prefill under load", fontsize=9, color=INK2)
    fig.subplots_adjust(top=0.945 if has_lt else 0.93)
    fig.savefig(path, dpi=130, facecolor=SURFACE, bbox_inches="tight")


def main():
    labels = sys.argv[1:] or ["ornith"]
    data, all_tasks = {}, []
    for lb in labels:
        scores, reqs, ev = load(lb)
        s, pt = summarize(lb, scores, reqs)
        ltp = RES / lb / "loadtest.json"
        lt = json.loads(ltp.read_text()) if ltp.exists() else None
        if lt:
            s["loadtest"] = [{k: v for k, v in r.items() if k != "raw"} for r in lt]
        data[lb] = dict(summary=s, per_task=pt, reqs=reqs, ev=ev, loadtest=lt)
        all_tasks += pt
    (RES / "summary.json").write_text(json.dumps({lb: data[lb]["summary"] for lb in labels}, indent=1))
    with open(RES / "per_task.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(all_tasks[0]))
        w.writeheader(); w.writerows(all_tasks)
    plot(data, RES / "benchmark.png")
    print(json.dumps({lb: data[lb]["summary"] for lb in labels}, indent=1))


if __name__ == "__main__":
    main()
