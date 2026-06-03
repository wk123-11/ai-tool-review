#!/usr/bin/env python3
"""Debug Toutiao image upload - try various formats"""
import urllib.request, json, os, uuid
from pathlib import Path

SITE_DIR = Path("/home/wk/ai-tool-review")
COOKIE_FILE = SITE_DIR / "scripts" / ".toutiao_cookie"
cookie = COOKIE_FILE.read_text().strip()

# Get csrftoken from cookie
csrftoken = ""
for part in cookie.split(";"):
    part = part.strip()
    if part.startswith("csrftoken="):
        csrftoken = part.split("=", 1)[1]
        break

HEADERS = {
    'Cookie': cookie,
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0',
    'Origin': 'https://mp.toutiao.com',
    'Referer': 'https://mp.toutiao.com/profile_v4/graphic/publish',
}

# Get token
req = urllib.request.Request('https://mp.toutiao.com/mp/agw/article_material/token/create', headers=HEADERS)
resp = urllib.request.urlopen(req, timeout=15)
token_info = json.loads(resp.read().decode())
token = token_info['token_info']['token']
print(f"Token: {token[:20]}...")

# Read image
img_path = SITE_DIR / "images" / "ai-brain.jpg"
with open(img_path, 'rb') as f:
    img_data = f.read()
print(f"Image: {img_path.name}, {len(img_data)} bytes")

# Try with X-CSRFToken header
headers_with_csrf = {**HEADERS, 'X-CSRFToken': csrftoken}

# Try multiple field name combinations
field_configs = [
    {"token": token, "file": ("ai-brain.jpg", img_data, "image/jpeg")},
    {"token": token, "image": ("ai-brain.jpg", img_data, "image/jpeg")},
    {"token": token, "upload_file": ("ai-brain.jpg", img_data, "image/jpeg")},
    {"token": token, "img": ("ai-brain.jpg", img_data, "image/jpeg")},
    {"token": token, "photo": ("ai-brain.jpg", img_data, "image/jpeg")},
    {"token": token, "file": ("blob", img_data, "image/jpeg")},
]

for fields in field_configs:
    # Build multipart
    boundary = '----WebKitFormBoundary' + uuid.uuid4().hex[:16]
    
    body_parts = []
    file_field_name = None
    file_info = None
    for k, v in fields.items():
        if isinstance(v, tuple):
            file_field_name = k
            file_info = v
        else:
            body_parts.append(f'--{boundary}\r\n')
            body_parts.append(f'Content-Disposition: form-data; name="{k}"\r\n\r\n')
            body_parts.append(f'{v}\r\n')
    
    body_parts.append(f'--{boundary}\r\n')
    body_parts.append(f'Content-Disposition: form-data; name="{file_field_name}"; filename="{file_info[0]}"\r\n')
    body_parts.append(f'Content-Type: {file_info[2]}\r\n\r\n')
    body_parts_bytes = [p.encode() if isinstance(p, str) else p for p in body_parts]
    body_parts_bytes.append(file_info[1])
    body_parts_bytes.append(f'\r\n--{boundary}--\r\n'.encode())
    
    body = b''.join(body_parts_bytes)
    
    url = 'https://mp.toutiao.com/mp/agw/article_material/photo/upload_picture'
    req = urllib.request.Request(url, data=body, headers={
        **headers_with_csrf,
        'Content-Type': f'multipart/form-data; boundary={boundary}',
    }, method='POST')
    
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode())
            code = result.get('code')
            if code == 0:
                url_val = result.get('data', {}).get('url', '')
                print(f'✅ [field={file_field_name}] code=0 url={url_val[:80]}...')
            else:
                msg = result.get('message', '?')
                print(f'❌ [field={file_field_name}] code={code} msg={msg}')
    except Exception as e:
        print(f'💥 [field={file_field_name}] Error: {type(e).__name__}: {e}')
