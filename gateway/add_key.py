#!/usr/bin/env python3
"""Issue a gateway API key.

usage: venv/bin/python add_key.py <user> <client>
  e.g. add_key.py alice@example.com opencode

Prints the new key once; restart the gateway to load it:
  systemctl --user restart llm-gateway
"""
import json
import os
import secrets
import sys

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys.json")
user, client = sys.argv[1], sys.argv[2]
keys = json.load(open(path))
key = f"sk-{client}-{secrets.token_hex(16)}"
keys[key] = {"user": user, "client": client}
old = os.umask(0o077)
json.dump(keys, open(path, "w"), indent=2)
os.umask(old)
print(key)
