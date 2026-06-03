#!/usr/bin/env python3
"""Upload baseline JPEG to Toutiao"""
import urllib.request, json, os, uuid

SITE_DIR = "/home/wk/ai-tool-review"
cookie = open(f"{SITE_DIR}/scripts/.toutiao_cookie").read().strip()

HEADERS = {
    'Cookie': cookie,
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Origin': 'https://mp.toutiao.com',
    'Referer': 'https://mp.toutiao.com/profile_v4/graphic/publish',
}

# Get token
req = urllib.request.Request('https://mp.toutiao.com/mp/agw/article_material/token/create', headers=HEADERS)
resp = urllib.request.urlopen(req, timeout=15)
token = json.loads(resp.read().decode())['token_info']['token']
print(f"Token: {token[:20]}...")

# Use baseline JPEG
img_path = "/tmp/baseline_ai_brain.jpg"
with open(img_path, 'rb') as f:
    img_data = f.read()
print(f"Image: baseline JPEG, {len(img_data)} bytes")

# Upload with proper multipart
boundary = '----WebKitFormBoundary' + uuid.uuid4().hex[:16]
body = b''
body += f'--{boundary}\r\nContent-Disposition: form-data; name="token"\r\n\r\n{token}\r\n'.encode()
body += f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="ai-brain.jpg"\r\nContent-Type: image/jpeg\r\n\r\n'.encode()
body += img_data
body += f'\r\n--{boundary}--\r\n'.encode()

url = 'https://mp.toutiao.com/mp/agw/article_material/photo/upload_picture'
req = urllib.request.Request(url, data=body, headers={
    **HEADERS,
    'Content-Type': f'multipart/form-data; boundary={boundary}',
}, method='POST')

try:
    resp = urllib.request.urlopen(req, timeout=15)
    result = json.loads(resp.read().decode())
    print(f"Response: code={result.get('code')} msg={result.get('message','')}")
    if result.get('code') == 0:
        data = result.get('data', {})
        print(f"URL: {data.get('url', 'N/A')}")
        print(f"Web URL: {data.get('web_url', 'N/A')}")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2)[:300])
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
