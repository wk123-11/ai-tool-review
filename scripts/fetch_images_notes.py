#!/usr/bin/env python3
"""Download candidate Unsplash images for the AI读书笔记 article, skip duplicates."""
import hashlib, os, urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
IMG = "/home/wk/ai-tool-review/images"

CANDIDATES = [
    ("photo-1512820790803-83ca734da794", "note2026-books-stack.jpg"),
    ("photo-1524995997946-a1c2e315a42f", "note2026-open-book.jpg"),
    ("photo-1544716278-ca5e3f4abd8c", "note2026-reading-book.jpg"),
    ("photo-1517842645767-c639042777db", "note2026-notebook-writing.jpg"),
    ("photo-1543002588-bfa74002ed7e", "note2026-book-desk.jpg"),
    ("photo-1495446815901-a7297e633e8d", "note2026-library-books.jpg"),
    ("photo-1455390582262-044cdead277a", "note2026-handwritten-notes.jpg"),
    ("photo-1532012197267-da84d127e765", "note2026-book-pages.jpg"),
    ("photo-1507842217343-583bb7270b66", "note2026-library-shelf.jpg"),
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
