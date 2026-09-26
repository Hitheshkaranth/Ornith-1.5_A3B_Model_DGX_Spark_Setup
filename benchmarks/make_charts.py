"""Render the README charts from the result JSON files in this folder.

usage: python3 benchmarks/make_charts.py
"""

import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

# Validated default categorical palette (dataviz skill, references/palette.md), slots 1-2.
QWEN38, ORNITH = "#2a78d6", "#eb6834"
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e1e0d9"
LABELS = ["Qwen3.8-35B-A3B\n(previous repo, no MTP)", "Ornith-1.5-35B-A3B\n(this repo, MTP on)"]

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 11,
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "axes.edgecolor": GRID, "axes.labelcolor": INK2, "text.color": INK,
    "xtick.color": INK2, "ytick.color": INK2,
    "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
    "axes.grid": True, "axes.grid.axis": "y", "grid.color": GRID, "grid.linewidth": 0.8,
    "axes.axisbelow": True,
})


def bar_panel(ax, title, values, fmt, unit):
    bars = ax.bar(LABELS, values, color=[QWEN38, ORNITH], width=0.55,
                  edgecolor=SURFACE, linewidth=2)
    ax.set_title(title, loc="left", fontsize=12, color=INK, pad=12, fontweight="bold")
    ax.set_ylabel(unit)
    ax.set_ylim(0, max(values) * 1.18)
    ax.tick_params(axis="x", length=0)
    for b, v in zip(bars, values):
        ax.text(b.get_x() + b.get_width() / 2, v + max(values) * 0.02, fmt.format(v),
                ha="center", va="bottom", color=INK, fontsize=11, fontweight="bold")


def throughput():
    r = json.load(open(os.path.join(HERE, "throughput_result.json")))["results"]
    a = r["qwen3.8-35b-a3b (previous repo, no MTP)"]
    b = r["ornith-1.5-35b-a3b (this repo, MTP on)"]
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.6))
    bar_panel(axes[0], "Decode speed, 1 user",
              [a["users_1"]["aggregate_tok_s"], b["users_1"]["aggregate_tok_s"]], "{:.1f}", "tokens / s")
    bar_panel(axes[1], "Aggregate decode, 16 users",
              [a["users_16"]["aggregate_tok_s"], b["users_16"]["aggregate_tok_s"]], "{:.1f}", "tokens / s")
    bar_panel(axes[2], "Per-user decode, 16 users",
              [a["users_16"]["per_user_tok_s"], b["users_16"]["per_user_tok_s"]], "{:.1f}", "tokens / s")
    fig.suptitle("Throughput on one DGX Spark (GB10) - vLLM 0.24.0, 512 output tokens per request",
                 x=0.01, ha="left", fontsize=13, color=INK)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "throughput_comparison.png"), dpi=150)
    print("wrote throughput_comparison.png")


def reasoning():
    paths = {k: os.path.join(HERE, f"reasoning_result_{k}.json") for k in ("qwen38", "ornith")}
    if not all(os.path.exists(p) for p in paths.values()):
        print("skipping reasoning chart: need reasoning_result_qwen38.json and reasoning_result_ornith.json")
        return
    a, b = (json.load(open(paths[k])) for k in ("qwen38", "ornith"))
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.6))
    bar_panel(axes[0], "GSM8K accuracy (100)",
              [a["gsm8k"]["accuracy"] * 100, b["gsm8k"]["accuracy"] * 100], "{:.0f}%", "% correct")
    bar_panel(axes[1], "MATH-500 accuracy (100, integer answers)",
              [a["math500"]["accuracy"] * 100, b["math500"]["accuracy"] * 100], "{:.0f}%", "% correct")
    bar_panel(axes[2], "Avg. long-form output length",
              [a["longform"]["avg_tokens"], b["longform"]["avg_tokens"]], "{:,.0f}", "tokens (cap 32,768)")
    for ax in axes[:2]:
        ax.set_ylim(0, 105)
    fig.suptitle("Reasoning and output length - same prompts, sampling and limits for both models",
                 x=0.01, ha="left", fontsize=13, color=INK)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "reasoning_comparison.png"), dpi=150)
    print("wrote reasoning_comparison.png")


def knowledge():
    paths = {k: os.path.join(HERE, f"knowledge_result_{k}.json") for k in ("qwen38", "ornith")}
    if not all(os.path.exists(p) for p in paths.values()):
        print("skipping knowledge chart: need knowledge_result_qwen38.json and knowledge_result_ornith.json")
        return
    a, b = (json.load(open(paths[k])) for k in ("qwen38", "ornith"))
    fig, ax = plt.subplots(figsize=(6.5, 4.6))
    bar_panel(ax, "MMLU-Pro accuracy (700-question stratified sample)",
              [a["accuracy"] * 100, b["accuracy"] * 100], "{:.1f}%", "% correct")
    ax.set_ylim(0, 100)
    fig.suptitle("Knowledge: MMLU-Pro", x=0.01, ha="left", fontsize=13, color=INK)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "knowledge_comparison.png"), dpi=150)
    print("wrote knowledge_comparison.png")


throughput()
reasoning()
knowledge()
