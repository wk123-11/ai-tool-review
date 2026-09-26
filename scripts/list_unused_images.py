#!/usr/bin/env python3
"""List images in images/ that are NOT referenced by any _posts/*.md and match a keyword."""
import os, re, sys

ROOT = "/home/wk/ai-tool-review"
IMG = os.path.join(ROOT, "images")
kw = sys.argv[1] if len(sys.argv) > 1 else ""

used = set()
for fn in os.listdir(os.path.join(ROOT, "_posts")):
    if fn.endswith(".md"):
        txt = open(os.path.join(ROOT, "_posts", fn), encoding="utf-8", errors="ignore").read()
        for m in re.findall(r"/images/([^)\"'\s]+)", txt):
            used.add(m)

tot = 0
for fn in sorted(os.listdir(IMG)):
    if kw and kw not in fn:
        continue
    if fn not in used:
        print("UNUSED", fn, os.path.getsize(os.path.join(IMG, fn)) // 1024, "KB")
        tot += 1
print("total unused:", tot, "| total images:", len(os.listdir(IMG)), "| referenced:", len(used))
