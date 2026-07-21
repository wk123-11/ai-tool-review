#!/usr/bin/env python3
"""Test if GitHub token is valid."""
import subprocess, os, json

script_dir = os.path.dirname(os.path.abspath(__file__))
ghtoken_path = os.path.join(script_dir, '.ghtoken')

with open(ghtoken_path) as f:
    token = f.read().strip()

print(f"Token: {token[:20]}...{token[-10:]}")
print(f"Token length: {len(token)}")

env = os.environ.copy()
env['https_proxy'] = 'http://172.21.16.1:7890'

result = subprocess.run(
    ['curl', '-s', '-w', '\n%{http_code}', '-H', f'Authorization: Bearer {token}',
     'https://api.github.com/user'],
    env=env, capture_output=True, text=True
)
output = result.stdout.strip()
lines = output.rsplit('\n', 1)
http_code = lines[-1] if lines else 'unknown'
body = '\n'.join(lines[:-1]) if len(lines) > 1 else ''
print(f"HTTP code: {http_code}")
try:
    data = json.loads(body)
    print(f"Login: {data.get('login', 'N/A')}")
    print(f"Type: {data.get('type', 'N/A')}")
except:
    print(f"Body (truncated): {body[:200]}")

result2 = subprocess.run(
    ['curl', '-s', '-w', '\n%{http_code}', '-H', f'Authorization: Bearer {token}',
     'https://api.github.com/repos/wk123-11/ai-tool-review'],
    env=env, capture_output=True, text=True
)
output2 = result2.stdout.strip()
lines2 = output2.rsplit('\n', 1)
http_code2 = lines2[-1] if lines2 else 'unknown'
body2 = '\n'.join(lines2[:-1]) if len(lines2) > 1 else ''
print(f"\nRepo access HTTP: {http_code2}")
print(f"Body: {body2[:200]}")
