#!/usr/bin/env bash
# vLLM server for ornith-ai/Ornith-1.5-35B-A3B-NVFP4 (Qwen3_5Moe fine-tune; same architecture,
# image and flags as the Qwen3.8-35B-A3B server in ../vllm-qwen3.8-a3b).
# Unlike Qwen3.8 (a text-only distill), this checkpoint ships a real vision tower
# (333 model.visual.* tensors + vision_config in config.json), so --language-model-only
# is NOT set here -- setting it disables image input entirely ("At most 0 image(s)...").
# MTP speculative decoding enabled: the checkpoint ships mtp.* weights (mtp_num_hidden_layers=1),
# and vLLM auto-detects the qwen3_5_mtp draft arch from model_type=qwen3_5_moe when the
# speculative-config `model` points at this same checkpoint dir.
# --moe-backend is left at "auto" (not forced to marlin): the MTP drafter's expert layers are
# unquantized BF16 and marlin only supports quantized MoE, so forcing marlin crashes on drafter
# load. "auto" still picks marlin for the main model's NVFP4 experts on this GPU (no native FP4).
# GB10 unified-memory box: keep --gpu-memory-utilization <= 0.70 or concurrency collapses,
# and don't run this alongside another 0.70 container (vllm-qwen38-a3b on :8002, vllm on :8000).
# max-num-seqs raised from 16 (Qwen3.8's value) to 20: KV cache logged
# "Maximum concurrency for 262,144 tokens per request: 19.75x", so there's memory headroom
# for 20 concurrent sequences even at full context; most real requests use far less.
set -euo pipefail

IMAGE="vllm-ornith-a3b:local"   # NVIDIA vLLM 26.07 + xgrammar 0.2.4 fix; built from this repo's Dockerfile
NAME="vllm-ornith-a3b"
PORT="${PORT:-8004}"
# Published only for the metering gateway (localhost) and Prometheus (docker bridge).
BIND_ADDRS="${BIND_ADDRS:-127.0.0.1 172.17.0.1}"
PUBLISH=()
for addr in $BIND_ADDRS; do PUBLISH+=(-p "$addr:$PORT:8000"); done
# Bearer key on /v1/* held only by the gateway (~/Documents/llm-gateway/upstream.key).
: "${VLLM_API_KEY:=$(cat ~/Documents/llm-gateway/upstream.key 2>/dev/null || true)}"
export VLLM_API_KEY
ENV_ARGS=()
[ -n "$VLLM_API_KEY" ] && ENV_ARGS+=(-e VLLM_API_KEY)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODEL_DIR="$SCRIPT_DIR/models/Ornith-1.5-35B-A3B-NVFP4"

docker build -t "$IMAGE" "$SCRIPT_DIR"

docker rm -f "$NAME" 2>/dev/null || true

exec docker run -d \
  --name "$NAME" \
  --restart "${RESTART:-no}" \
  --gpus all \
  --ipc host \
  "${PUBLISH[@]}" \
  "${ENV_ARGS[@]}" \
  -v "$MODEL_DIR":/models/ornith-1.5-35b-a3b:ro \
  "$IMAGE" \
  python3 -m vllm.entrypoints.openai.api_server \
    --model /models/ornith-1.5-35b-a3b \
    --served-model-name ornith-1.5-35b-a3b \
    --gpu-memory-utilization 0.70 \
    --max-model-len 262144 \
    --max-num-seqs 20 \
    --max-num-batched-tokens 8192 \
    --enable-prefix-caching \
    --kv-cache-dtype fp8 \
    --speculative-config '{"model": "/models/ornith-1.5-35b-a3b", "num_speculative_tokens": 1}' \
    --reasoning-parser qwen3 \
    --enable-auto-tool-choice \
    --tool-call-parser qwen3_coder \
    --host 0.0.0.0 \
    --port 8000
