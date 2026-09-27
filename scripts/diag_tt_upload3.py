#!/usr/bin/env python3
import sys, json, time, io, uuid, mimetypes, urllib.request, urllib.error
from pathlib import Path
sys.path.insert(0, "/home/wk/ai-tool-review/scripts")
from secrets_config import PROJECT_ROOT, load_toutiao_cookie
import toutiao_api as T

cookie = load_toutiao_cookie()
p = PROJECT_ROOT / "images" / "draw2026-color-palette.jpg"

def attempt(url, extra_headers=None, field="image", extra_fields=None):
    body, ctype = T._multipart(p.name, p.read_bytes(), "image/jpeg")
    # inject extra fields
    if extra_fields:
        pass
    h = T.headers(cookie)
    h.update({"Content-Type": ctype, "x-secsdk-csrf-token": T._csrf(cookie)})
    if extra_headers:
        h.update(extra_headers)
    req = urllib.request.Request(url, data=body, headers=h, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")
    except Exception as e:
        return None, repr(e)

urls = [
    "https://mp.toutiao.com/spice/image?upload_source=20020002&aid=1231&device_platform=web",
    "https://mp.toutiao.com/spice/image?upload_source=20020002&aid=1231&device_platform=web&category=article",
]
for u in urls:
    print("===", u)
    print(attempt(u))

# multipart with extra form fields (aid, device_platform, upload_source as fields)
def multipart_fields(name, filedata, fields):
    boundary = "----WebKitFormBoundary" + uuid.uuid4().hex[:16]
    b = io.BytesIO()
    for k, v in fields.items():
        b.write(f"--{boundary}\r\n".encode())
        b.write(f'Content-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
    b.write(f"--{boundary}\r\n".encode())
    b.write(f'Content-Disposition: form-data; name="image"; filename="{name}"\r\n'.encode())
    b.write(b"Content-Type: image/jpeg\r\n\r\n")
    b.write(filedata)
    b.write(f"\r\n--{boundary}--\r\n".encode())
    return b.getvalue(), f"multipart/form-data; boundary={boundary}"

body, ctype = multipart_fields(p.name, p.read_bytes(),
    {"upload_source": "20020002", "aid": "1231", "device_platform": "web"})
h = T.headers(cookie)
h.update({"Content-Type": ctype, "x-secsdk-csrf-token": T._csrf(cookie)})
req = urllib.request.Request("https://mp.toutiao.com/spice/image", data=body, headers=h, method="POST")
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        print("=== fields-form:", r.status, r.read().decode("utf-8","ignore")[:400])
except urllib.error.HTTPError as e:
    print("=== fields-form HTTP", e.code, e.read().decode("utf-8","ignore")[:400])
except Exception as e:
    print("=== fields-form err", e)
