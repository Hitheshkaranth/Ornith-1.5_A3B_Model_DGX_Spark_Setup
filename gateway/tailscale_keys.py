#!/usr/bin/env python3
"""Issue one gateway API key per device on your tailnet.

usage: venv/bin/python tailscale_keys.py [--out devices.csv] [--include-offline]
                                         [--tailscale /path/to/tailscale]

Reads `tailscale status --json`, skips this machine, and for every peer that
doesn't have a key yet adds {"user": <device>, "client": "device-<device>"}
to keys.json. Existing device keys are kept, so it's safe to re-run as
devices join. Writes a CSV (device, tailscale_ip, api_key) to hand the keys
out. Keep it private (it's created with mode 600, and git-ignored).

Restart the gateway afterwards to load the new keys:
  systemctl --user restart llm-gateway
"""
import argparse
import csv
import json
import os
import secrets
import shutil
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
KEYS_PATH = os.path.join(HERE, "keys.json")

ap = argparse.ArgumentParser()
ap.add_argument("--out", default=os.path.join(HERE, "devices.csv"))
ap.add_argument("--include-offline", action="store_true", default=True,
                help="also issue keys for peers that are currently offline (default)")
ap.add_argument("--online-only", dest="include_offline", action="store_false")
ap.add_argument("--tailscale", default=shutil.which("tailscale") or "tailscale")
args = ap.parse_args()

status = json.loads(subprocess.check_output([args.tailscale, "status", "--json"]))
keys = json.load(open(KEYS_PATH)) if os.path.exists(KEYS_PATH) else {}
by_client = {v["client"]: k for k, v in keys.items()}

rows, created = [], 0
for peer in status.get("Peer", {}).values():
    if not args.include_offline and not peer.get("Online"):
        continue
    device = peer["DNSName"].split(".")[0] or peer["HostName"].lower()
    client = f"device-{device}"
    key = by_client.get(client)
    if key is None:
        key = f"sk-{client}-{secrets.token_hex(16)}"
        keys[key] = {"user": device, "client": client}
        created += 1
    rows.append((device, peer["TailscaleIPs"][0], key))

old = os.umask(0o077)
json.dump(keys, open(KEYS_PATH, "w"), indent=2)
with open(args.out, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["device", "tailscale_ip", "api_key"])
    w.writerows(sorted(rows))
os.umask(old)

print(f"{len(rows)} devices, {created} new keys -> {args.out}")
print("restart the gateway to load them: systemctl --user restart llm-gateway")
