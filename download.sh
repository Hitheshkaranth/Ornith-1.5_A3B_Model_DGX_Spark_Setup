#!/usr/bin/env bash
# Fetch ornith-ai's own NVFP4 build (ModelOpt MIXED_PRECISION: W4A16 NVFP4 routed+shared experts,
# FP8 attention/linear-attn, FP8 KV). Plain HTTP; Xet transfers stalled on this box.
cd "$(dirname "$0")"
export HF_HUB_DISABLE_XET=1
exec ~/.local/bin/uvx --from huggingface_hub hf download ornith-ai/Ornith-1.5-35B-A3B-NVFP4 \
  --local-dir models/Ornith-1.5-35B-A3B-NVFP4 --max-workers 8
