#!/usr/bin/env python3
"""Fix image URLs in published Zhihu article"""
import re, json, sys, urllib.request, urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.resolve()))
from zhihu_zse96 import get_xzse96

cookie_str = Path(Path(__file__).parent / ".zhihu_cookie").read_text().strip()
cookies = {}
for part in cookie_str.split(";"):
    p = part.strip()
    if "=" in p:
        k,v = p.split("=",1)
        cookies[k.strip()] = v.strip()
d_c0 = cookies.get("d_c0","")

from publish_zhihu import markdown_to_zhihu_html, parse_markdown_post

title, body = parse_markdown_post(Path(__file__).parent.parent / "_posts/2026-05-31-ai-video-tools-battlefield.md")
html = markdown_to_zhihu_html(body)

# Map image alt text to filenames
alt_to_file = [
    ("AI视频工具全景", "future-tech.jpg"),
    ("Runway Gen-4.5", "tech-data.jpg"),
    ("可灵 Kling 3.0", "ai-creative.jpg"),
    ("Vidu Q3", "coding.jpg"),
    ("Pika 2.5", "video-production.jpg"),
    ("Sora 已关停", "ai-brain.jpg"),
]

for alt_text, filename in alt_to_file:
    pattern = r'(<img\s+src=")[^"]*(" alt="' + re.escape(alt_text) + '")'
    replacement = r'\1https://raw.githubusercontent.com/wk123-11/ai-tool-review/main/images/' + filename + r'\2'
    html = re.sub(pattern, replacement, html)

remaining = html.count('image-tt-private')
print(f"Remaining old URLs: {remaining}")
print(f"Title: {title}")
print(f"HTML length: {len(html)}")

article_id = "2044636626773599828"

def call(method, api_path, body):
    sig = get_xzse96(d_c0, api_path)
    h = {
        'Cookie': cookie_str,
        'x-zse-93': '101_3_3.0',
        'x-zse-96': sig,
        'x-requested-with': 'fetch',
        'Referer': 'https://zhuanlan.zhihu.com/',
        'Origin': 'https://zhuanlan.zhihu.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Content-Type': 'application/json;charset=UTF-8',
        'Accept': 'application/json, text/plain, */*',
    }
    data = json.dumps(body, ensure_ascii=False).encode('utf-8') if body else None
    url = f"https://zhuanlan.zhihu.com{api_path}"
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body_bytes = resp.read()
            if body_bytes.strip():
                r = json.loads(body_bytes.decode('utf-8'))
                print(f"  {method} {api_path} => {resp.status}: {json.dumps(r, ensure_ascii=False)[:300]}")
                return r
            else:
                print(f"  {method} {api_path} => {resp.status} (empty body)")
                return {"status": "ok"}
    except urllib.error.HTTPError as e:
        err = e.read().decode('utf-8', errors='replace')[:500]
        print(f"  {method} {api_path} => {e.code}: {err}")
        return None

print(f"\nEditing published article {article_id}...")

# Try PATCH on draft endpoint first (this is how the original script updates drafts)
print("\nStep 1: PATCH draft content...")
r = call("PATCH", f"/api/articles/{article_id}/draft", {"title": title, "content": html})

if r is not None:
    # Try to publish the updated draft
    print("\nStep 2: PUT publish...")
    r = call("PUT", f"/api/articles/{article_id}/publish", {})
    if r and "id" in r:
        print(f"\n  ✅ Article fixed: https://zhuanlan.zhihu.com/p/{article_id}")
    elif r:
        print(f"\n  Response: {json.dumps(r, ensure_ascii=False)[:300]}")
else:
    print("\n  ❌ PATCH failed, article may not be editable")
