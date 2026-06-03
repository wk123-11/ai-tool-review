#!/usr/bin/env python3
"""Try various upload formats for Toutiao"""
import urllib.request, json, uuid
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.text import MIMEText

SITE_DIR = Path("/home/wk/ai-tool-review")
cookie = (SITE_DIR / "scripts" / ".toutiao_cookie").read_text().strip()

HEADERS = {
    'Cookie': cookie,
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Origin': 'https://mp.toutiao.com',
    'Referer': 'https://mp.toutiao.com/profile_v4/graphic/publish',
}

# Get token
req = urllib.request.Request('https://mp.toutiao.com/mp/agw/article_material/token/create', headers=HEADERS)
token = json.loads(urllib.request.urlopen(req, timeout=15).read())['token_info']['token']
print(f"Token: {token[:20]}")

img_bytes = (SITE_DIR / "images" / "ai-brain.jpg").read_bytes()
print(f"Image: {len(img_bytes)} bytes")

def try_upload(name, body, ct):
    url = 'https://mp.toutiao.com/mp/agw/article_material/photo/upload_picture'
    req = urllib.request.Request(url, data=body, headers={**HEADERS, 'Content-Type': ct}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            r = json.loads(resp.read().decode())
            c = r.get('code')
            m = r.get('message', '')
            if c == 0:
                u = r.get('data', {}).get('url', '')
                print(f'OK {name}: {u[:80]}')
            else:
                print(f'XX {name}: code={c} {m}')
    except Exception as e:
        print(f'EE {name}: {type(e).__name__}: {e}')

# Method 1: MIME multipart with correct encoding
b = '----WebKitFormBoundary' + uuid.uuid4().hex
part1 = ('--%s\r\n'
         'Content-Disposition: form-data; name="token"\r\n\r\n'
         '%s\r\n') % (b, token)
part2 = ('--%s\r\n'
         'Content-Disposition: form-data; name="file"; filename="blob"\r\n'
         'Content-Type: application/octet-stream\r\n\r\n') % b
part3 = '\r\n--%s--\r\n' % b
body = part1.encode() + part2.encode() + img_bytes + part3.encode()
try_upload('method1-multipart', body, 'multipart/form-data; boundary=' + b)

# Method 2: Same but with image/jpeg
b = '----WebKitFormBoundary' + uuid.uuid4().hex
part1 = ('--%s\r\n'
         'Content-Disposition: form-data; name="token"\r\n\r\n'
         '%s\r\n') % (b, token)
part2 = ('--%s\r\n'
         'Content-Disposition: form-data; name="file"; filename="blob"\r\n'
         'Content-Type: image/jpeg\r\n\r\n') % b
part3 = '\r\n--%s--\r\n' % b
body = part1.encode() + part2.encode() + img_bytes + part3.encode()
try_upload('method2-jpeg', body, 'multipart/form-data; boundary=' + b)

# Method 3: different field order (file first, then token)
b = '----WebKitFormBoundary' + uuid.uuid4().hex
part1 = ('--%s\r\n'
         'Content-Disposition: form-data; name="file"; filename="blob"\r\n'
         'Content-Type: image/jpeg\r\n\r\n') % b
part2 = ('\r\n--%s\r\n'
         'Content-Disposition: form-data; name="token"\r\n\r\n'
         '%s\r\n--%s--\r\n') % (b, token, b)
body = part1.encode() + img_bytes + part2.encode()
try_upload('method3-revorder', body, 'multipart/form-data; boundary=' + b)

# Method 4: raw POST as image/jpeg
try_upload('method4-raw', img_bytes, 'image/jpeg')
