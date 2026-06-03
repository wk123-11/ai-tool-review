#!/usr/bin/env python3
"""
上传图片到头条号图床，然后发布文章（替换图片URL为头条CDN URL）
用法: python3 scripts/upload_images.py _posts/2026-05-31-ai-video-tools-battlefield.md
"""
import sys, os, re, json, urllib.request, urllib.parse, io, uuid, mimetypes
from pathlib import Path
from datetime import datetime

SITE_DIR = Path("/home/wk/ai-tool-review")
COOKIE_FILE = SITE_DIR / "scripts" / ".toutiao_cookie"
IMG_DIR = SITE_DIR / "images"

cookie = COOKIE_FILE.read_text().strip()

HEADERS = {
    'Cookie': cookie,
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0',
    'Origin': 'https://mp.toutiao.com',
    'Referer': 'https://mp.toutiao.com/profile_v4/graphic/publish',
}

import urllib.error

def extract_csrf_token():
    """从 cookie 中提取 x-secsdk-csrf-token"""
    cookie = COOKIE_FILE.read_text().strip()
    m = re.search(r'passport_csrf_token=([^;]+)', cookie)
    if m:
        return m.group(1)
    return ''

def encode_multipart_formdata_single(filename, filedata, content_type):
    """构建单个文件上传的 multipart/form-data 请求体（字段名: image）"""
    boundary = '----WebKitFormBoundary' + uuid.uuid4().hex[:16]
    body = io.BytesIO()
    
    body.write(f'--{boundary}\r\n'.encode())
    body.write(f'Content-Disposition: form-data; name="image"; filename="{filename}"\r\n'.encode())
    body.write(f'Content-Type: {content_type}\r\n\r\n'.encode())
    body.write(filedata)
    body.write(f'\r\n--{boundary}--\r\n'.encode())
    
    return body.getvalue(), f'multipart/form-data; boundary={boundary}'

def upload_image(img_path, token=None):
    """上传一张图片到头条号（使用 /spice/image 端点）"""
    img_path = Path(img_path)
    if not img_path.exists():
        print(f"❌ Image not found: {img_path}")
        return None
    
    with open(img_path, 'rb') as f:
        img_data = f.read()
    
    ext = img_path.suffix.lower()
    mime_type = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
    }.get(ext, 'image/jpeg')
    
    body, ct = encode_multipart_formdata_single(img_path.name, img_data, mime_type)
    
    url = 'https://mp.toutiao.com/spice/image?upload_source=20020002&aid=1231&device_platform=web'
    csrf_token = extract_csrf_token()
    headers = {
        **HEADERS,
        'Content-Type': ct,
        'x-secsdk-csrf-token': csrf_token,
    }
    
    req = urllib.request.Request(url, data=body, headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            if result.get('code') == 0:
                data = result.get('data', {})
                # New endpoint returns image_url (includes CDN + signed params)
                cdn_url = data.get('image_url') or data.get('url')
                if cdn_url:
                    print(f"   ✅ {img_path.name} → {cdn_url[:80]}...")
                    return cdn_url
                else:
                    print(f"   ⚠️  No URL in response: {json.dumps(result, ensure_ascii=False)[:200]}")
                    return None
            else:
                print(f"   ❌ Upload failed (code {result.get('code')}): {result.get('message', 'unknown')}")
                print(f"   Response: {json.dumps(result, ensure_ascii=False)[:200]}")
                return None
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace')
        print(f"   ❌ HTTP {e.code}: {body[:200]}")
        return None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def parse_markdown_post(filepath):
    """解析 Jekyll markdown 文章"""
    path = Path(filepath)
    text = path.read_text(encoding='utf-8')
    
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", text, re.DOTALL)
    if match:
        frontmatter = match.group(1)
        body = match.group(2).strip()
        t = re.search(r"title:\s*(.+)", frontmatter)
        title = t.group(1).strip().strip('"').strip("'") if t else ""
    else:
        title = ""
        body = text.strip()
    
    return title, body

def markdown_to_toutiao_html(markdown_text):
    """将 Markdown 转为头条号兼容的 HTML"""
    lines = markdown_text.split("\n")
    html_parts = []
    in_list = False
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Image
        img_match = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)$", stripped)
        if img_match:
            alt = img_match.group(1)
            src = img_match.group(2)
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            html_parts.append(f'<p><img src="{src}" alt="{alt}" style="max-width:100%"></p>')
            continue
        
        # Headers
        if stripped.startswith("## "):
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            html_parts.append(f"<h2>{stripped[3:]}</h2>")
        elif stripped.startswith("### "):
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            html_parts.append(f"<h3>{stripped[4:]}</h3>")
        elif stripped.startswith("#### "):
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            html_parts.append(f"<h4>{stripped[5:]}</h4>")
        # Paragraph
        elif stripped and not stripped.startswith("#") and not stripped.startswith("- ") and not stripped.startswith("* "):
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            if re.match(r"^\d+\.\s", stripped):
                html_parts.append(f"<p>{stripped}</p>")
            else:
                html_parts.append(f"<p>{stripped}</p>")
        # List items
        elif stripped.startswith("- ") or stripped.startswith("* "):
            if not in_list:
                html_parts.append("<ul>")
                in_list = True
            html_parts.append(f"<li>{stripped[2:]}</li>")
        # Empty lines
        elif not stripped:
            if in_list:
                html_parts.append("</ul>")
                in_list = False
    
    if in_list:
        html_parts.append("</ul>")
    
    full_html = "".join(html_parts)
    full_html = full_html.replace("<p>", '<p data-track="1">', 1)
    
    return full_html

def publish_article(title, html_content):
    """发布图文文章"""
    url = "https://mp.toutiao.com/mp/agw/article/publish?source=mp&type=article&aid=1231"
    
    word_count = len(re.sub(r"<[^>]+>", "", html_content))
    
    data = urllib.parse.urlencode({
        "content": html_content,
        "title": title,
        "article_type": "0",
        "save": "1",
        "source": "29",
        "extra": json.dumps({
            "content_source": 100000000402,
            "content_word_cnt": word_count,
            "is_multi_title": 0,
            "sub_titles": [],
            "gd_ext": {
                "entrance": "",
                "from_page": "publisher_mp",
                "enter_from": "PC",
                "device_platform": "mp",
                "is_message": 0,
            },
            "tuwen_wtt_trans_flag": "0",
        }, ensure_ascii=False),
    }).encode("utf-8")
    
    headers = {
        **HEADERS,
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        "Accept": "application/json, text/plain, */*",
    }
    
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode("utf-8"))
        
        if result.get("code") == 0:
            pgc_id = result.get("data", {}).get("pgc_id", "")
            print(f"✅ 头条号发布成功!")
            print(f"   title: {title}")
            print(f"   pgc_id: {pgc_id}")
            print(f"   字数: {word_count}")
            return True, pgc_id
        else:
            err_msg = result.get("message", result.get("reason", "unknown"))
            print(f"❌ 发布失败: {err_msg}")
            print(f"   full response: {json.dumps(result, ensure_ascii=False)[:300]}")
            return False, None


def main():
    if len(sys.argv) < 2:
        print("用法: python3 scripts/upload_images.py <markdown_file>")
        sys.exit(1)
    
    filepath = sys.argv[1]
    title, body = parse_markdown_post(filepath)
    
    if not title:
        print("❌ 无法提取标题")
        sys.exit(1)
    
    print(f"📝 文章: {title}")
    
    # Step 1: Find all image URLs that reference local files
    local_images = re.findall(r'!\[([^\]]*)\]\(/images/([^)]+)\)', body)
    gh_images = re.findall(r'!\[([^\]]*)\]\(https://raw\.githubusercontent\.com/[^/]+/[^/]+/[^/]+/images/([^)]+)\)', body)
    
    # Merge dedup
    image_files = set()
    image_map = {}  # old_url -> alt_text
    
    for alt, fname in local_images:
        image_files.add(fname)
        image_map[f'/images/{fname}'] = alt
    
    for alt, fname in gh_images:
        image_files.add(fname)
    
    print(f"🖼️  发现 {len(image_files)} 张图片")
    
    if not image_files:
        print("⚠️  没有本地图片需要上传，直接发布...")
        html = markdown_to_toutiao_html(body)
        publish_article(title, html)
        return
    
    # Step 2: Upload each image (new /spice/image endpoint doesn't need token)
    uploaded = {}
    for fname in sorted(image_files):
        img_path = IMG_DIR / fname
        print(f"📤 上传 {fname}...")
        cdn_url = upload_image(img_path)
        if cdn_url:
            uploaded[fname] = cdn_url
    
    if not uploaded:
        print("❌ 所有图片上传失败!")
        sys.exit(1)
    
    print(f"\n✅ 成功上传 {len(uploaded)}/{len(image_files)} 张图片")
    
    # Step 4: Replace URLs in body
    new_body = body
    for fname, cdn_url in uploaded.items():
        # Replace both local and GitHub raw URLs
        new_body = new_body.replace(f'/images/{fname}', cdn_url)
        new_body = new_body.replace(
            f'https://raw.githubusercontent.com/wk123-11/ai-tool-review/main/images/{fname}',
            cdn_url
        )
    
    # Step 5: Convert to HTML and publish
    html = markdown_to_toutiao_html(new_body)
    success, pgc_id = publish_article(title, html)
    
    if success:
        log_path = SITE_DIR / "scripts" / ".toutiao_published_ids"
        with open(log_path, "a") as f:
            f.write(f"{datetime.now().isoformat()}|{pgc_id}|{title} (with images)\n")
        print(f"\n🎉 含图版已发布!")
        print(f"   pgc_id: {pgc_id}")
    else:
        print("\n❌ 发布失败")


if __name__ == "__main__":
    main()
