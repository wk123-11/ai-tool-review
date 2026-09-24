#!/usr/bin/env python3
"""Download candidate Unsplash images for the AI配音有声书 article, skip duplicates."""
import hashlib, os, urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
IMG = "/home/wk/ai-tool-review/images"

CANDIDATES = [
    ("photo-1598488035139-bdbb2231ce04", "voice2026-studio-mic.jpg"),
    ("photo-1478737270239-2f02b77fc618", "voice2026-audio-mixer.jpg"),
    ("photo-1516280440614-37939bbacd81", "voice2026-headphones-music.jpg"),
    ("photo-1590602847861-f357a9332bbc", "voice2026-podcast-mic.jpg"),
    ("photo-1487215078519-e21cc028cb29", "voice2026-recording-booth.jpg"),
    ("photo-1598653222000-6b7b7a552625", "voice2026-waveform.jpg"),
    ("photo-1571330735066-03aaa9429d89", "voice2026-podcast-setup.jpg"),
    ("photo-1511671782779-c97d3d27a1d4", "voice2026-headphones-desk.jpg"),
    ("photo-1521590832167-7bcbfaa6381f", "voice2026-audiobook-book.jpg"),
    ("photo-1507842217343-583bb7270b66", "voice2026-library-reading.jpg"),
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
