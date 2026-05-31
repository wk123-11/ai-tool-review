#!/usr/bin/env python3
"""
头条号自动发布脚本
发布图文文章到头条号 via /mp/agw/article/publish
用法: python3 scripts/publish_toutiao.py <markdown_file>
"""
import sys
import os
import re
import json
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime

SITE_DIR = Path("/home/wk/ai-tool-review")
COOKIE_FILE = SITE_DIR / "scripts" / ".toutiao_cookie"

def load_cookie():
    """从文件加载 cookie"""
    if not COOKIE_FILE.exists():
        print("❌ Cookie file not found! Run: echo 'cookie_string' > scripts/.toutiao_cookie")
        sys.exit(1)
    content = COOKIE_FILE.read_text().strip()
    return content

def parse_markdown_post(filepath):
    """解析 Jekyll markdown 文章，提取 frontmatter 和内容"""
    path = Path(filepath)
    if not path.exists():
        print(f"❌ File not found: {filepath}")
        sys.exit(1)
    
    text = path.read_text(encoding="utf-8")
    
    # Parse Jekyll frontmatter
    title = ""
    date_str = ""
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", text, re.DOTALL)
    if match:
        frontmatter = match.group(1)
        body = match.group(2).strip()
        # Extract title
        t = re.search(r"title:\s*(.+)", frontmatter)
        if t:
            title = t.group(1).strip().strip('"').strip("'")
        # Extract date
        d = re.search(r"date:\s*(.+)", frontmatter)
        if d:
            date_str = d.group(1).strip()
    else:
        # No frontmatter, use first line as title
        lines = text.strip().split("\n")
        title = lines[0].strip().strip("#").strip()
        body = "\n".join(lines[1:]).strip()
    
    return title, body

def markdown_to_toutiao_html(markdown_text):
    """将 Markdown 转为头条号兼容的 HTML"""
    lines = markdown_text.split("\n")
    html_parts = []
    in_list = False
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
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
            # Check if it's a numbered list
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
    
    # Wrap all content in a div for now (no data-track)
    full_html = "".join(html_parts)
    
    # Add data-track="1" to first <p> like the real editor does
    full_html = full_html.replace("<p>", '<p data-track="1">', 1)
    
    return full_html

def publish_article(title, html_content, cookie):
    """发布图文文章到头条号"""
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
        "Cookie": cookie,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0",
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://mp.toutiao.com",
        "Referer": "https://mp.toutiao.com/profile_v4/graphic/publish",
    }
    
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    
    try:
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
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP错误: {e.code} {e.reason}")
        return False, None
    except urllib.error.URLError as e:
        print(f"❌ 网络错误: {e.reason}")
        return False, None

def main():
    if len(sys.argv) < 2:
        print("用法: python3 scripts/publish_toutiao.py <markdown_file>")
        print("也可以从 stdin 读取: python3 scripts/publish_toutiao.py -")
        sys.exit(1)
    
    filepath = sys.argv[1]
    
    if filepath == "-":
        stdin_data = sys.stdin.read().strip()
        if not stdin_data:
            print("❌ No input from stdin")
            sys.exit(1)
        # Extract title from first heading
        title = "AI工具派文章"
        for line in stdin_data.split("\n"):
            line = line.strip()
            if line.startswith("# "):
                title = line[2:].strip()
                break
            elif line.startswith("## "):
                title = line[3:].strip()
                break
        body = stdin_data
    else:
        title, body = parse_markdown_post(filepath)
    
    if not title:
        print("❌ Could not extract title")
        sys.exit(1)
    
    print(f"📝 准备发布: {title}")
    
    # Convert markdown to HTML
    html_content = markdown_to_toutiao_html(body)
    
    # Load cookie
    cookie = load_cookie()
    
    # Publish
    success, pgc_id = publish_article(title, html_content, cookie)
    
    if success:
        # Save the pgc_id to a log file for reference
        log_path = SITE_DIR / "scripts" / ".toutiao_published_ids"
        with open(log_path, "a") as f:
            f.write(f"{datetime.now().isoformat()}|{pgc_id}|{title}\n")

if __name__ == "__main__":
    main()
