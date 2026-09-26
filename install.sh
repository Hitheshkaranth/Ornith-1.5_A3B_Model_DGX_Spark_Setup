#!/usr/bin/env bash
# One-line installer for Ornith-1.5-35B-A3B (ornith-ai's official NVFP4 build) on a
# DGX Spark (GB10) or any single Blackwell GPU box.
#
#   curl -fsSL https://raw.githubusercontent.com/Hitheshkaranth/Ornith-1.5_A3B_Model_DGX_Spark_Setup/main/install.sh | bash
#
# Clones this repo (or updates it if already present in the current
# directory), downloads the pre-quantized weights, and starts the server via
# run.sh. Every step skips work that's already done, so it's safe to re-run.
set -euo pipefail

REPO_URL="${ORNITH_REPO_URL:-https://github.com/Hitheshkaranth/Ornith-1.5_A3B_Model_DGX_Spark_Setup.git}"
DIR="Ornith-1.5_A3B_Model_DGX_Spark_Setup"

echo "==> Checking prerequisites..."

if ! command -v git >/dev/null 2>&1; then
  echo "git is required. Install it first (e.g. 'sudo apt-get install -y git')." >&2
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required. Install it first: https://docs.docker.com/engine/install/" >&2
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "Docker daemon isn't reachable (is it running, and do you have permission to use it?)." >&2
  exit 1
fi

if ! docker run --rm --gpus all nvidia/cuda:12.6.0-base-ubuntu22.04 nvidia-smi >/dev/null 2>&1; then
  echo "GPU not visible to Docker. Install the NVIDIA Container Toolkit, then re-run this script:" >&2
  echo "  https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html" >&2
  exit 1
fi

if ! command -v uvx >/dev/null 2>&1 && [ ! -x "$HOME/.local/bin/uvx" ]; then
  echo "==> Installing uv (used to run the Hugging Face CLI)..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi

echo "==> Prerequisites OK."

if [ -d "$DIR/.git" ]; then
  echo "==> $DIR already exists here, pulling latest..."
  git -C "$DIR" pull --ff-only
else
  echo "==> Cloning $REPO_URL..."
  git clone "$REPO_URL" "$DIR"
fi

cd "$DIR"

echo "==> Downloading the official NVFP4 checkpoint (~22 GiB, resumes if interrupted)..."
./download.sh

echo "==> Building image and starting the server (MTP speculative decoding + vision enabled)..."
./run.sh

echo
echo "==> Done. Tail logs with: docker logs -f vllm-ornith-a3b"
echo "==> Server will be reachable at http://localhost:8004/v1 once startup completes (~5 minutes)."
