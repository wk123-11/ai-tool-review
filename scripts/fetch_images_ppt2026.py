#!/usr/bin/env python3
"""Download candidate Unsplash images for the 2026 AI PPT tools article, skip duplicates."""
import hashlib, os, urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
IMG = "/home/wk/ai-tool-review/images"

# Presentation / slides / deck building themed photos
CANDIDATES = [
    ("photo-1542744173-8e7e53415bb0", "ppt2026-team-presentation.jpg"),
    ("photo-1553877522-43269d4ea984", "ppt2026-whiteboard-plan.jpg"),
    ("photo-1559136555-9303baea8ebd", "ppt2026-stage-presenting.jpg"),
    ("photo-1460925895917-afdab827c52f", "ppt2026-laptop-charts.jpg"),
    ("photo-1522202176988-66273c2fd55f", "ppt2026-people-laptops.jpg"),
    ("photo-1517245386807-bb43f82c33c4", "ppt2026-desk-laptop.jpg"),
    ("photo-1531403009284-440f080d1e12", "ppt2026-analytics-charts.jpg"),
    ("photo-1551836022-d5d88e9218df", "ppt2026-conference-room.jpg"),
    ("photo-1531973576160-7125cd663d86", "ppt2026-speaking-audience.jpg"),
    ("photo-1587614382346-4ec70e388b28", "ppt2026-slide-editing.jpg"),
    ("photo-1626785774573-4b799315345d", "ppt2026-design-workspace.jpg"),
    ("photo-1516321318423-f06f85e504b3", "ppt2026-presenting-screen.jpg"),
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
    ok = 0
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
        ok += 1
        print(f"OK   {name} ({len(data)//1024} KB)")
    print(f"saved {ok} images")


if __name__ == "__main__":
    main()
