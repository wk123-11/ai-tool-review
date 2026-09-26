#!/usr/bin/env python3
"""Supplemental fetch of strongly-relevant Unsplash images for the AI绘图 article."""
import hashlib, os, json, subprocess
from urllib.parse import quote

IMG = "/home/wk/ai-tool-review/images"
PROXY = "http://172.21.16.1:7890"
env = dict(os.environ)
env["https_proxy"] = PROXY
env["http_proxy"] = PROXY

QUERIES = [
    ("ai-art", "draw2026-ai-artwork"),
    ("digital-illustration", "draw2026-digital-illustration"),
    ("artist-digital-tablet", "draw2026-artist-tablet"),
    ("graphic-art-abstract", "draw2026-abstract-graphic"),
]


def curl(url, out=None):
    cmd = ["curl", "-sL", "--max-time", "60", url]
    if out:
        cmd += ["-o", out]
        subprocess.run(cmd, check=True, env=env)
        return None
    return subprocess.run(cmd, capture_output=True, env=env).stdout


def md5(b):
    return hashlib.md5(b).hexdigest()


def main():
    existing = {}
    for fn in os.listdir(IMG):
        p = os.path.join(IMG, fn)
        if os.path.isfile(p):
            try:
                existing[md5(open(p, "rb").read())] = fn
            except Exception:
                pass
    used = set()
    for q, name in QUERIES:
        api = f"https://unsplash.com/napi/search/photos?query={quote(q)}&per_page=10&orientation=landscape"
        try:
            data = json.loads(curl(api))
        except Exception as e:
            print(f"SEARCH FAIL {q}: {e}")
            continue
        for r in data.get("results", []):
            pid = r["id"]
            alt = (r.get("alt_description") or "")[:80]
            url = f"https://images.unsplash.com/photo-{pid}?w=1200&q=80" if pid.startswith("photo-") \
                else f"https://unsplash.com/photos/{pid}/download?w=1200"
            tmp = "/tmp/_u2.jpg"
            try:
                curl(url, tmp)
                blob = open(tmp, "rb").read()
            except Exception as e:
                print(f"  dl fail {pid}: {e}")
                continue
            if len(blob) < 8000:
                continue
            h = md5(blob)
            if h in existing or h in used:
                continue
            open(os.path.join(IMG, name + ".jpg"), "wb").write(blob)
            used.add(h)
            print(f"OK  {name}.jpg ({len(blob)//1024} KB) [{q}] {pid} :: {alt}")
            break


if __name__ == "__main__":
    main()
