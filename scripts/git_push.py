#!/usr/bin/env python3
"""Push to GitHub using token from .ghtoken file."""
import subprocess, sys, os, urllib.parse

token_path = os.path.join(os.path.dirname(__file__), '.ghtoken')
with open(token_path) as f:
    token = f.read().strip()

encoded_token = urllib.parse.quote(token, safe='')
url = f"https://wk123-11:{encoded_token}@github.com/wk123-11/ai-tool-review.git"

env = os.environ.copy()
env['https_proxy'] = 'http://172.21.16.1:7890'

result = subprocess.run(
    ['git', 'push', url, 'main'],
    cwd=os.path.join(os.path.dirname(__file__), '..'),
    env=env,
    capture_output=True, text=True
)
print(result.stdout)
if result.stderr:
    print(result.stderr, file=sys.stderr)
sys.exit(result.returncode)
