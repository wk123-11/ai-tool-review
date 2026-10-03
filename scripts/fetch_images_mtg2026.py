#!/usr/bin/env python3
"""Download candidate Unsplash images for the AI meeting-notes article, skip duplicates."""
import hashlib, os, urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
IMG = "/home/wk/ai-tool-review/images"

CANDIDATES = [
    ("photo-1517245386807-bb43f82c33c4", "mtg2026-team-meeting.jpg"),
    ("photo-1552664730-d307ca884978", "mtg2026-team-discussion.jpg"),
    ("photo-1600880292203-757bb62b4baf", "mtg2026-business-meeting.jpg"),
    ("photo-1519389950473-47ba0277781c", "mtg2026-laptops-meeting.jpg"),
    ("photo-1543269865-cbf427effbad", "mtg2026-meeting-table.jpg"),
    ("photo-1560472354-b33ff0c44a43", "mtg2026-office-meeting.jpg"),
    ("photo-1521737604893-d14cc237f11d", "mtg2026-collaboration.jpg"),
    ("photo-1557804506-669a67965ba0", "mtg2026-meeting-notes.jpg"),
    ("photo-1531973576160-7125cd663d86", "mtg2026-video-call.jpg"),
    ("photo-1478737270239-2f02b77fc618", "mtg2026-microphone.jpg"),
    ("photo-1589903308904-1010c2294adc", "mtg2026-audio-waveform.jpg"),
    ("photo-1590602847861-f357a9332bbc", "mtg2026-audio-recording.jpg"),
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
