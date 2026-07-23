#!/usr/bin/env python3
"""Git push test with detailed debugging."""
import subprocess
import os

token_path = os.path.join(os.path.dirname(__file__), '.ghtoken')
with open(token_path) as f:
    token = f.read().strip()

env = os.environ.copy()
env['https_proxy'] = 'http://172.21.16.1:7890'
env['GIT_TERMINAL_PROMPT'] = '0'  # disable prompts

url = f"https://wk123-11:{token}@github.com/wk123-11/ai-tool-review.git"

# First clear the stored credential
subprocess.run(
    ['git', 'credential', 'reject'],
    input=f"protocol=https\nhost=github.com\n\n",
    text=True, capture_output=True,
    env=env
)

result = subprocess.run(
    ['git', 'push', url, 'main'],
    cwd=os.path.join(os.path.dirname(__file__), '..'),
    env=env,
    capture_output=True, text=True
)
print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
print("RETURN:", result.returncode)
