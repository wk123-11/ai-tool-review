#!/usr/bin/env python3
"""Test GitHub token validity"""
with open('/home/wk/ai-tool-review/scripts/.ghtoken') as f:
    token = f.read().strip()

import urllib.request, json
req = urllib.request.Request(
    "https://api.github.com/user",
    headers={"Authorization": f"Bearer {token}", "User-Agent": "Hermes"}
)
try:
    resp = urllib.request.urlopen(req, timeout=10)
    data = json.loads(resp.read())
    print(f"User: {data.get('login', 'unknown')}")
    print(f"Token valid: YES")
except urllib.error.HTTPError as e:
    print(f"Token valid: NO (HTTP {e.code}: {e.reason})")
    body = e.read().decode()
    print(f"Body: {body[:200]}")
except Exception as e:
    print(f"Error: {e}")
