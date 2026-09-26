#!/usr/bin/env python3
"""Download fresh Unsplash images via curl (proxy) for the AI绘图工具 article."""
import hashlib, os, json, subprocess

IMG = "/home/wk/ai-tool-review/images"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
PROXY = "http://172.21.16.1:7890"

QUERIES = [
    ("digital-art-creation", "draw2026-digital-canvas"),
    ("drawing-tablet-stylus", "draw2026-tablet-stylus"),
    ("graphic-designer-workspace", "draw2026-designer-workspace"),
    ("color-palette-paint", "draw2026-color-palette"),
    ("generative-art", "draw2026-generative-art"),
    ("illustration-software-screen", "draw2026-illustration-software"),
]


env = dict(os.environ)
env["https_proxy"] = PROXY
env["http_proxy"] = PROXY


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
    print("existing images:", len(existing))
    used = set()
    for q, name in QUERIES:
        from urllib.parse import quote
        api = f"https://unsplash.com/napi/search/photos?query={quote(q)}&per_page=8&orientation=landscape"
        try:
            data = json.loads(curl(api))
        except Exception as e:
            print(f"SEARCH FAIL {q}: {e}")
            continue
        done = False
        for r in data.get("results", []):
            pid = r["id"]
            url = f"https://images.unsplash.com/photo-{pid}?w=1200&q=80" if pid.startswith("photo-") \
                else f"https://unsplash.com/photos/{pid}/download?w=1200"
            tmp = "/tmp/_u.jpg"
            try:
                curl(url, tmp)
                blob = open(tmp, "rb").read()
            except Exception as e:
                print(f"  dl fail {pid}: {e}")
                continue
            if len(blob) < 8000:
                print(f"  skip {pid}: too small")
                continue
            h = md5(blob)
            if h in existing or h in used:
                print(f"  DUP {pid}")
                continue
            open(os.path.join(IMG, name + ".jpg"), "wb").write(blob)
            used.add(h)
            print(f"OK  {name}.jpg ({len(blob)//1024} KB) [{q} / {pid}]")
            done = True
            break
        if not done:
            print(f"NO IMAGE for {q}")


if __name__ == "__main__":
    main()
