#!/usr/bin/env python3
import sys, io, uuid, urllib.request, urllib.error
sys.path.insert(0, "/home/wk/ai-tool-review/scripts")
from secrets_config import PROJECT_ROOT, load_toutiao_cookie
import toutiao_api as T

cookie = load_toutiao_cookie()
p = PROJECT_ROOT / "images" / "draw2026-color-palette.jpg"
data = p.read_bytes()

def try_upload(qs):
    body, ctype = T._multipart(p.name, data, "image/jpeg")
    h = T.headers(cookie)
    h.update({"Content-Type": ctype, "x-secsdk-csrf-token": T._csrf(cookie)})
    url = "https://mp.toutiao.com/spice/image" + ("?" + qs if qs else "")
    req = urllib.request.Request(url, data=body, headers=h, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            b = r.read().decode("utf-8", "ignore")
        return b[:160]
    except urllib.error.HTTPError as e:
        return "HTTP %s %s" % (e.code, e.read().decode("utf-8", "ignore")[:120])
    except Exception as e:
        return "ERR " + repr(e)

sources = [20020002, 20020001, 20020003, 20020004, 20020005, 1000000001, 1000000002,
           20000001, 20000002, 10001, 10101, 10201, 11001, 12001, 13001]
for s in sources:
    print(s, "->", try_upload(f"upload_source={s}&aid=1231&device_platform=web"))
