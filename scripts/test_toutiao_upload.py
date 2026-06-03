#!/usr/bin/env python3
"""Try to find Toutiao's image upload endpoint"""
import urllib.request, urllib.parse, json, os, sys

cookie = open('/home/wk/ai-tool-review/scripts/.toutiao_cookie').read().strip()
headers = {
    'Cookie': cookie,
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36',
    'Origin': 'https://mp.toutiao.com',
    'Referer': 'https://mp.toutiao.com/profile_v4/graphic/publish',
}

# Test various potential upload endpoints
endpoints = [
    '/mp/agw/article/upload_image',
    '/mp/agw/article/upload_img',
    '/mp/agw/upload/image',
    '/mp/agw/upload',
    '/upload/image/',
    '/upload/image',
    '/upload/',
    '/api/publish/image_upload',
    '/mp/agw/article/publish/image_upload',
    '/image/upload',
    '/api/v2/publish/image_upload',
    '/mp/agw/creative/article/upload',
    '/mp/agw/upload_image',
    '/upload_article_image',
    '/article/image/upload',
]

base = 'https://mp.toutiao.com'

for ep in endpoints:
    url = base + ep
    try:
        req = urllib.request.Request(url, method='GET', headers=headers)
        resp = urllib.request.urlopen(req, timeout=8)
        body = resp.read().decode('utf-8', errors='replace')[:200]
        print(f'✅ {ep}: HTTP {resp.status}')
        print(f'   Body: {body}')
    except urllib.error.HTTPError as e:
        code = e.code
        body = e.read().decode('utf-8', errors='replace')[:100]
        print(f'⚠️  {ep}: HTTP {code} — {body}')
    except Exception as e:
        print(f'❌ {ep}: {type(e).__name__}: {e}')
