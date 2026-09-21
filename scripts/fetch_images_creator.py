#!/usr/bin/env python3
"""Download candidate Unsplash images for the 自媒体人AI工具 article, skip duplicates."""
import hashlib, os, urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
IMG = "/home/wk/ai-tool-review/images"

CANDIDATES = [
    ("photo-1536240478700-b869070f9279", "creator2026-video-editing.jpg"),
    ("photo-1574717024653-61fd2cf4d44d", "creator2026-editor-timeline.jpg"),
    ("photo-1590602847861-f357a9332bbc", "creator2026-podcast-mic.jpg"),
    ("photo-1626785774573-4b799315345d", "creator2026-design-canvas.jpg"),
    ("photo-1551288049-bebda4e38f71", "creator2026-analytics-dash.jpg"),
    ("photo-1499750310107-5fef28a66643", "creator2026-creator-desk.jpg"),
    ("photo-1478737270239-2f02b77fc618", "creator2026-studio-mic-alt.jpg"),
    ("photo-1460925895917-afdab827c52f", "creator2026-analytics-alt.jpg"),
    ("photo-1587440871875-191322ee64b0", "creator2026-design-alt.jpg"),
    ("photo-1611162616475-46b635cb6868", "creator2026-social-alt.jpg"),
    ("photo-1504384308090-c894fdcc538d", "creator2026-desk-alt.jpg"),
    ("photo-1519389950473-47ba0277781c", "creator2026-team-alt.jpg"),
]


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
    print(f"existing images: {len(existing)}")
    used = set()
    for pid, name in CANDIDATES:
        url = f"https://images.unsplash.com/{pid}?w=1200&q=80"
        try:
            data = urllib.request.urlopen(
                urllib.request.Request(url, headers={"User-Agent": UA}), timeout=45).read()
        except Exception as e:
            print(f"FAIL {name}: {e}")
            continue
        if len(data) < 8000:
            print(f"SKIP {name}: too small ({len(data)} bytes)")
            continue
        h = md5(data)
        if h in existing:
            print(f"DUP  {name}: identical to {existing[h]}")
            continue
        if h in used:
            print(f"DUP  {name}: duplicate within batch")
            continue
        open(os.path.join(IMG, name), "wb").write(data)
        used.add(h)
        print(f"OK   {name} ({len(data)//1024} KB)")


if __name__ == "__main__":
    main()
