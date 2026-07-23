#!/usr/bin/env python3
"""Debug git credential flow."""
import subprocess
import os
import urllib.request
import json

token_path = os.path.join(os.path.dirname(__file__), '.ghtoken')
with open(token_path) as f:
    line = f.read()
print(repr(line))
print(f"Length: {len(line)}")
token = line.strip()
print(f"Stripped length: {len(token)}")

# Test via URL
url = f"https://wk123-11:{token}@github.com/wk123-11/ai-tool-review.git"
env = os.environ.copy()
env['https_proxy'] = 'http://172.21.16.1:7890'

result = subprocess.run(
    ['git', 'ls-remote', url, 'HEAD'],
    capture_output=True, text=True, env=env
)
print(f"ls-remote stdout: {result.stdout}")
print(f"ls-remote stderr: {result.stderr}")
print(f"ls-remote return: {result.returncode}")
