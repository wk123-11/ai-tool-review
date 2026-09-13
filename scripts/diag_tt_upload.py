#!/usr/bin/env python3
"""Diagnostic: try several Toutiao image upload endpoint/param variants."""
import io, json, re, sys, uuid, urllib.error, urllib.request
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from secrets_config import load_toutiao_cookie

COOKIE = load_toutiao_cookie()
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/148 Safari/537.36'
IMG = Path(__file__).resolve().parents[1] / 'images' / 'ecom2026-shipping-boxes.jpg'
DATA = IMG.read_bytes()
CSRF = ''
m = re.search(r'(?:^|;\s*)passport_csrf_token=([^;]+)', COOKIE)
if m:
    CSRF = m.group(1)

def multipart(name, filedata, ct):
    b = '----WebKitFormBoundary' + uuid.uuid4().hex[:16]
    body = io.BytesIO()
    body.write(f'--{b}\r\n'.encode())
    body.write(f'Content-Disposition: form-data; name="image"; filename="{name}"\r\n'.encode())
    body.write(f'Content-Type: {ct}\r\n\r\n'.encode())
    body.write(filedata)
    body.write(f'\r\n--{b}--\r\n'.encode())
    return body.getvalue(), f'multipart/form-data; boundary={b}'

def post(url, extra_headers=None, field='image'):
    body, ct = multipart(IMG.name, DATA, 'image/jpeg')
    if field != 'image':
        body = body.replace(b'name="image"', f'name="{field}"'.encode())
    h = {'Cookie': COOKIE, 'User-Agent': UA, 'Origin': 'https://mp.toutiao.com',
         'Referer': 'https://mp.toutiao.com/profile_v4/graphic/publish',
         'Content-Type': ct, 'x-secsdk-csrf-token': CSRF}
    h.update(extra_headers or {})
    req = urllib.request.Request(url, data=body, headers=h, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode('utf-8', 'replace')[:400]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')[:400]
    except Exception as e:
        return 'ERR', str(e)[:300]

VARIANTS = [
    ('spice/aid/device', 'https://mp.toutiao.com/spice/image?upload_source=20020002&aid=1231&device_platform=web', None, 'image'),
    ('spice/no-aid', 'https://mp.toutiao.com/spice/image?upload_source=20020002', None, 'image'),
    ('spice/only-aid', 'https://mp.toutiao.com/spice/image?aid=1231&device_platform=web', None, 'image'),
    ('spice/upload_source=20020001', 'https://mp.toutiao.com/spice/image?upload_source=20020001&aid=1231&device_platform=web', None, 'image'),
    ('spice/field=upload', 'https://mp.toutiao.com/spice/image?upload_source=20020002&aid=1231&device_platform=web', None, 'upload'),
    ('spice/field=file', 'https://mp.toutiao.com/spice/image?upload_source=20020002&aid=1231&device_platform=web', None, 'file'),
    ('agw/photo/upload_picture', 'https://mp.toutiao.com/mp/agw/article_material/photo/upload_picture?aid=1231&device_platform=web', None, 'image'),
    ('ttupload/pro', 'https://mp.toutiao.com/spice/image?upload_source=20020002&aid=1231&device_platform=web&type=image', None, 'image'),
]
print('CSRF token present:', bool(CSRF))
for name, url, hdrs, field in VARIANTS:
    st, txt = post(url, hdrs, field)
    print(f'--- {name} [{field}] -> {st}\n{txt}\n')
