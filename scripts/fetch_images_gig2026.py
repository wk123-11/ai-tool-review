#!/usr/bin/env python3
"""Download candidate Unsplash images for the AI编程外包接单 article, skip duplicates."""
import hashlib, os, urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
IMG = "/home/wk/ai-tool-review/images"

CANDIDATES = [
    ("photo-1461749280684-dccba630e2f6", "gig2026-code-screen.jpg"),
    ("photo-1555949963-aa79dcee981c", "gig2026-programming-monitor.jpg"),
    ("photo-1587620962725-abab7fe55159", "gig2026-code-editor.jpg"),
    ("photo-1531482615713-2afd69097998", "gig2026-developer-desk.jpg"),
    ("photo-1498050108023-c5249f4df085", "gig2026-macbook-code.jpg"),
    ("photo-1516321318423-f06f85e504b3", "gig2026-analytics-laptop.jpg"),
    ("photo-1600880292203-757bb62b4baf", "gig2026-client-meeting.jpg"),
    ("photo-1454165804606-c3d57bc86b40", "gig2026-contract-desk.jpg"),
    ("photo-1554224155-6726b3ff858f", "gig2026-finance-calc.jpg"),
    ("photo-1450101499163-c8848c66ca85", "gig2026-notebook-plan.jpg"),
    ("photo-1521737604893-d14cc237f11d", "gig2026-team-standup.jpg"),
    ("photo-1517180102446-f3ece451e9d8", "gig2026-dark-code.jpg"),
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
