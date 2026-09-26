#!/usr/bin/env bash
# Install the metering gateway as a systemd user service.
#
#   ./gateway/setup.sh                      # listen on all interfaces, port 8080
#   GATEWAY_HOST=100.x.y.z ./gateway/setup.sh   # tailnet only (your Tailscale IP)
#
# Safe to re-run: existing keys.json / upstream.key / usage.db are kept.
set -euo pipefail
cd "$(dirname "$0")"
DIR="$PWD"

GATEWAY_HOST="${GATEWAY_HOST:-0.0.0.0}"
GATEWAY_PORT="${GATEWAY_PORT:-8080}"
GATEWAY_BACKENDS="${GATEWAY_BACKENDS:-http://127.0.0.1:8004}"

echo "==> Python environment"
if command -v uv >/dev/null 2>&1; then
  [ -d venv ] || uv venv -q venv
  uv pip install -q --python venv/bin/python -r requirements.txt
else
  [ -d venv ] || python3 -m venv venv
  venv/bin/pip install -q -r requirements.txt
fi

umask 077
if [ ! -f upstream.key ]; then
  echo "==> Generating upstream.key (the secret vLLM will require; only the gateway holds it)"
  python3 -c "import secrets;print('sk-vllm-upstream-'+secrets.token_hex(24))" > upstream.key
fi
if [ ! -f keys.json ]; then
  echo "==> Creating keys.json with an admin key"
  python3 - <<'EOF'
import json, secrets
key = f"sk-admin-{secrets.token_hex(16)}"
json.dump({key: {"user": "admin", "client": "admin"}}, open("keys.json", "w"), indent=2)
print("    admin key:", key)
EOF
fi
umask 022

echo "==> systemd user service (~/.config/systemd/user/llm-gateway.service)"
mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/llm-gateway.service <<EOF
[Unit]
Description=Metering gateway in front of local vLLM (per-user/per-device token usage)
After=network.target

[Service]
Type=simple
WorkingDirectory=$DIR
Environment=GATEWAY_HOST=$GATEWAY_HOST
Environment=GATEWAY_PORT=$GATEWAY_PORT
Environment=GATEWAY_BACKENDS=$GATEWAY_BACKENDS
ExecStart=$DIR/venv/bin/python $DIR/gateway.py
Restart=on-failure
RestartSec=3

[Install]
WantedBy=default.target
EOF
systemctl --user daemon-reload
systemctl --user enable --now llm-gateway
# Keep running after logout / start at boot without a login session.
loginctl enable-linger "$USER" 2>/dev/null || echo "    (run 'sudo loginctl enable-linger $USER' so it starts at boot)"

echo
echo "==> Gateway: http://$GATEWAY_HOST:$GATEWAY_PORT/v1   health: curl localhost:$GATEWAY_PORT/health"
echo "==> Next: restart vLLM so it requires the upstream key and is not reachable directly:"
echo "      VLLM_API_KEY=\$(cat $DIR/upstream.key) BIND_ADDRS=\"127.0.0.1 172.17.0.1\" ./run.sh"
