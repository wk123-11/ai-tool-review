#!/usr/bin/env python3
"""Probe Toutiao spice/image with different upload_source values and extra params."""
import io, re, sys, uuid, urllib.error, urllib.request
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from secrets_config import load_toutiao_cookie

COOKIE = load_toutiao_cookie()
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/148 Safari/537.36'
IMG = Path(__file__).resolve().parents[1] / 'images' / 'ecom2026-shipping-boxes.jpg'
DATA = IMG.read_bytes()
m = re.search(r'(?:^|;\s*)passport_csrf_token=([^;]+)', COOKIE)
CSRF = m.group(1) if m else ''

def post(url):
    b = '----WebKitFormBoundary' + uuid.uuid4().hex[:16]
    body = io.BytesIO()
    body.write(f'--{b}\r\n'.encode())
    body.write(f'Content-Disposition: form-data; name="image"; filename="{IMG.name}"\r\n'.encode())
    body.write(b'Content-Type: image/jpeg\r\n\r\n')
    body.write(DATA); body.write(f'\r\n--{b}--\r\n'.encode())
    h = {'Cookie': COOKIE, 'User-Agent': UA, 'Origin': 'https://mp.toutiao.com',
         'Referer': 'https://mp.toutiao.com/profile_v4/graphic/publish',
         'Content-Type': f'multipart/form-data; boundary={b}', 'x-secsdk-csrf-token': CSRF}
    req = urllib.request.Request(url, data=body.getvalue(), headers=h, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.read().decode('utf-8', 'replace')[:220]
    except urllib.error.HTTPError as e:
        return f'HTTP{e.code} ' + e.read().decode('utf-8', 'replace')[:200]
    except Exception as e:
        return 'ERR ' + str(e)[:200]

BASE = 'https://mp.toutiao.com/spice/image'
sources = ['20020002', '20020001', '20020003', '20020004', '20020005', '20020006',
           '20010001', '20030001', '30000001', '1000000', '1000001']
for s in sources:
    print(f'[{s}] {post(f"{BASE}?upload_source={s}&aid=1231&device_platform=web")}')

print('--- extra params on 20020002 ---')
extras = ['&image_source=0', '&image_source=1', '&type=0', '&from=mp',
          '&entrance=graphic_publish', '&source=29', '&image_type=0',
          '&need_ocr=0', '&upload_platform=web', '&scene=article']
for e in extras:
    print(f'[{e}] {post(f"{BASE}?upload_source=20020002&aid=1231&device_platform=web{e}")}')
