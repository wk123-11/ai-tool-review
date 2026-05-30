#!/usr/bin/env python3
"""Check GitHub token capabilities"""
import json, urllib.request, sys, os

TOKEN = os.environ.get("GH_TOKEN", "")
if not TOKEN:
    print("ERROR: Set GH_TOKEN env var")
    sys.exit(1)

def api(path, method="GET", data=None):
    req = urllib.request.Request(f"https://api.github.com{path}")
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "Hermes-bot")
    if data:
        req.data = json.dumps(data).encode()
        req.method = method
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"error": e.code, "body": e.read().decode()[:500]}

# 1. Check user
user = api("/user")
print(f"=== User ===")
print(f"Login: {user.get('login')}")
print(f"Name: {user.get('name')}")

# 2. Check existing repos
repos = api("/user/repos?per_page=5")
print(f"\n=== Existing Repos ({len(repos) if isinstance(repos, list) else 'error'}) ===")
if isinstance(repos, list):
    for r in repos:
        print(f"  - {r['name']}")
else:
    print(f"  {repos}")

# 3. Try creating a repo
print(f"\n=== Creating repo ===")
result = api("/user/repos", "POST", {
    "name": "ai-tool-review",
    "description": "AI工具派 - 精选AI工具评测",
    "private": False,
    "auto_init": False
})
if isinstance(result, dict) and "clone_url" in result:
    print(f"SUCCESS! Clone URL: {result['clone_url']}")
    print(f"HTML URL: {result['html_url']}")
else:
    print(f"Failed: {json.dumps(result, indent=2, ensure_ascii=False)[:800]}")
