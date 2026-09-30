#!/usr/bin/env python3
"""Download candidate Unsplash images for the 2026 AI 语音转文字 article, skip duplicates."""
import hashlib, os, urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
IMG = "/home/wk/ai-tool-review/images"

CANDIDATES = [
    ("photo-1589903308904-1010c2294adc", "stt2026-podcast-mic.jpg"),
    ("photo-1519389950473-47ba0277781c", "stt2026-team-laptops.jpg"),
    ("photo-1552664730-d307ca884978", "stt2026-meeting-discussion.jpg"),
    ("photo-1517048676732-d65bc937f952", "stt2026-conference-table.jpg"),
    ("photo-1521737604893-d14cc237f11d", "stt2026-interview-notes.jpg"),
    ("photo-1543269865-cbf427effbad", "stt2026-office-collab.jpg"),
    ("photo-1573164713988-8665fc963095", "stt2026-video-editing.jpg"),
    ("photo-1600880292203-757bb62b4baf", "stt2026-business-meeting.jpg"),
    ("photo-1522071820081-009f0129c71c", "stt2026-campus-study.jpg"),
    ("photo-1587825140708-dfaf72ae4b04", "stt2026-hands-laptop.jpg"),
    ("photo-1450101499163-c8848c66ca85", "stt2026-writing-transcript.jpg"),
    ("photo-1587560699334-cc4ff634909a", "stt2026-phone-recording.jpg"),
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
