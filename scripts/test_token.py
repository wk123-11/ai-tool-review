#!/usr/bin/env python3
"""Test GitHub token validity."""
import os, urllib.request, json

token_path = os.path.join(os.path.dirname(__file__), '.ghtoken')
with open(token_path) as f:
    token = f.read().strip()

# Test with GitHub API
req = urllib.request.Request('https://api.github.com/user')
req.add_header('Authorization', f'token {token}')
req.add_header('User-Agent', 'Hermes-Cron')

proxy_handler = urllib.request.ProxyHandler({'https': 'http://172.21.16.1:7890'})
opener = urllib.request.build_opener(proxy_handler)

try:
    resp = opener.open(req)
    data = json.loads(resp.read())
    print(f"Token user: {data['login']}")
    print(f"Token OK")
except urllib.request.HTTPError as e:
    print(f"HTTP {e.code}: {e.read().decode()}")
except Exception as e:
    print(f"Error: {e}")

# Also test the repo write access
req2 = urllib.request.Request(
    'https://api.github.com/repos/wk123-11/ai-tool-review',
    method='GET'
)
req2.add_header('Authorization', f'token {token}')
req2.add_header('User-Agent', 'Hermes-Cron')
try:
    resp = opener.open(req2)
    data = json.loads(resp.read())
    print(f"Repo: {data['full_name']}, access: {data.get('permissions', {})}")
except urllib.request.HTTPError as e:
    print(f"Repo check HTTP {e.code}: {e.read().decode()}")
