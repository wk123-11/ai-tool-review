#!/usr/bin/env python3
"""Second batch of Unsplash candidates for the AI meeting-notes article."""
import hashlib, os, urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
IMG = "/home/wk/ai-tool-review/images"

CANDIDATES = [
    ("photo-1522071820081-009f0129c71c", "mtg2026-teamwork2.jpg"),
    ("photo-1542744173-8e7e53415bb0", "mtg2026-meeting2.jpg"),
    ("photo-1551836022-d5d88e9218df", "mtg2026-boardroom.jpg"),
    ("photo-1517048676732-d65bc937f952", "mtg2026-group-meeting.jpg"),
    ("photo-1552581234-26160f608093", "mtg2026-conference2.jpg"),
    ("photo-1568992687947-868a62a9f521", "mtg2026-handshake-meeting.jpg"),
    ("photo-1516321318423-f06f85e504b3", "mtg2026-notes-laptop.jpg"),
    ("photo-1454165804606-c3d57bc86b40", "mtg2026-documents.jpg"),
    ("photo-1573164713988-8665fc963095", "mtg2026-woman-laptop.jpg"),
    ("photo-1541746972996-4e0b0f43e02a", "mtg2026-desk-notes.jpg"),
    ("photo-1521791136064-7986c2920216", "mtg2026-handshake.jpg"),
    ("photo-1525182008055-f88b95ff7980", "mtg2026-workshop.jpg"),
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
