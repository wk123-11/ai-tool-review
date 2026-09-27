#!/usr/bin/env python3
"""Diagnose Toutiao image upload failure."""
import sys, json, re, urllib.request, urllib.error
sys.path.insert(0, "/home/wk/ai-tool-review/scripts")
from secrets_config import PROJECT_ROOT, load_toutiao_cookie
from toutiao_api import upload_image, headers, _csrf

cookie = load_toutiao_cookie()
print("cookie length:", len(cookie))
keys = [p.split("=", 1)[0].strip() for p in cookie.split(";") if "=" in p]
print("cookie keys:", keys)
print("csrf token found:", bool(_csrf(cookie)), repr(_csrf(cookie))[:40])

# try a simple session health check
try:
    req = urllib.request.Request("https://mp.toutiao.com/mp/agw/creator/home/count",
                                 headers=headers(cookie))
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read().decode("utf-8", "ignore")
    print("home/count raw:", body[:400])
except urllib.error.HTTPError as e:
    print("home/count HTTP", e.code, e.read().decode("utf-8", "ignore")[:300])
except Exception as e:
    print("home/count error:", e)

try:
    url = upload_image(PROJECT_ROOT / "images" / "draw2026-color-palette.jpg", cookie)
    print("UPLOAD OK:", url)
except Exception as e:
    print("UPLOAD FAIL:", e)
