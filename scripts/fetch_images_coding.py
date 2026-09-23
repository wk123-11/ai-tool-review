#!/usr/bin/env python3
"""Download candidate Unsplash images for the AI编程助手 article, skip duplicates."""
import hashlib, os, urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
IMG = "/home/wk/ai-tool-review/images"

CANDIDATES = [
    ("photo-1555066931-4365d14bab8c", "code2026-screen-lines.jpg"),
    ("photo-1461749280684-dccba630e2f6", "code2026-editor-dark.jpg"),
    ("photo-1542831371-29b0f74f9713", "code2026-code-closeup.jpg"),
    ("photo-1516116216624-53e697fedbea", "code2026-ide-window.jpg"),
    ("photo-1587620962725-abab7fe55159", "code2026-html-monitor.jpg"),
    ("photo-1571171637578-41bc2dd41cd2", "code2026-terminal-work.jpg"),
    ("photo-1550439062-609e1531270e", "code2026-monitor-standup.jpg"),
    ("photo-1517180102446-f3ece451e9d8", "code2026-pair-programming.jpg"),
    ("photo-1531482615713-2afd69097998", "code2026-desk-review.jpg"),
    ("photo-1504639725590-34d0984388bd", "code2026-laptop-code.jpg"),
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
