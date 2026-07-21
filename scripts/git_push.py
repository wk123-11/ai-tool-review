#!/usr/bin/env python3
"""Push to GitHub using token from .ghtoken file."""
import subprocess, os, sys

script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.join(script_dir, '..')
ghtoken_path = os.path.join(script_dir, '.ghtoken')

with open(ghtoken_path) as f:
    token = f.read().strip()

env = os.environ.copy()
env['https_proxy'] = 'http://172.21.16.1:7890'
env['GIT_ASKPASS'] = os.path.join(script_dir, 'git-askpass.sh')

# First set the remote URL
subprocess.run(['git', 'remote', 'set-url', 'origin',
    f'https://wk123-11:ghp_placeholder@github.com/wk123-11/ai-tool-review.git'],
    cwd=root_dir, capture_output=True)

# Now push - git will use the askpass helper to provide credentials
result = subprocess.run(
    ['git', 'push', '-u', 'origin', 'main'],
    cwd=root_dir, env=env, capture_output=True, text=True
)
print(result.stdout)
if result.stderr:
    print(result.stderr[:800])
sys.exit(result.returncode)
