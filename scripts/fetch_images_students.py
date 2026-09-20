#!/usr/bin/env python3
"""Download candidate Unsplash images, skip duplicates of existing images/ (by md5)."""
import hashlib, os, sys, urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
IMG = "/home/wk/ai-tool-review/images"

# (unsplash photo id, output name)
CANDIDATES = [
    ("photo-1503676260728-1c00da094a0b", "stu2026-classroom-study.jpg"),
    ("photo-1456513080510-7bf3a84b82f8", "stu2026-study-books.jpg"),
    ("photo-1434030216411-0b793f4b4173", "stu2026-notes-writing.jpg"),
    ("photo-1522202176988-66273c2fd55f", "stu2026-study-laptop.jpg"),
    ("photo-1513258496099-48168024aec0", "stu2026-desk-laptop.jpg"),
    ("photo-1481627834876-b7833e8f5570", "stu2026-library-shelf.jpg"),
    ("photo-1543269865-cbf427effbad", "stu2026-group-study.jpg"),
    ("photo-1497633762265-9d179a990aa6", "stu2026-textbooks.jpg"),
    ("photo-1454165804606-c3d57bc86b40", "stu2026-desk-planning.jpg"),
    ("photo-1517486808906-6ca8b3f04846", "stu2026-library-desk.jpg"),
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
            print(f"DUP  {name}: identical to existing {existing[h]}, skipped")
            continue
        if h in used:
            print(f"DUP  {name}: duplicate within batch, skipped")
            continue
        open(os.path.join(IMG, name), "wb").write(data)
        used.add(h)
        print(f"OK   {name} ({len(data)//1024} KB)")


if __name__ == "__main__":
    main()
