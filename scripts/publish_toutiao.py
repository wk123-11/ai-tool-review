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


def _inline_format(text):
    """处理行内格式：加粗、斜体、行内代码、链接"""
    # Bold **text** (must be before italic to avoid overlap)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # Italic *text* (single asterisk, not inside words)
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', text)
    # Inline code `code`
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
    # Links [text](url)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" rel="nofollow">\1</a>', text)
    return text


def _parse_table(lines, start_idx):
    """从 start_idx 开始解析一个 markdown 表格，返回 (html, end_idx)"""
    rows = []
    i = start_idx
    while i < len(lines):
        stripped = lines[i].strip()
        if not stripped.startswith("|"):
            break
        # Skip separator row (|--|--|)
        if re.match(r"^\|[\s\-:]+\|", stripped):
            i += 1
            continue
        # Parse table row
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        rows.append(cells)
        i += 1

    if not rows:
        return "", start_idx

    html = '<table style="width:100%;border-collapse:collapse;margin:12px 0;font-size:14px;">\n'
    # Header row
    html += "<thead><tr>\n"
    for cell in rows[0]:
        html += '<th style="border:1px solid #ddd;padding:8px;background:#f5f5f5;font-weight:bold;text-align:left;">' + _inline_format(cell) + "</th>\n"
    html += "</tr></thead>\n"
    # Body rows
    if len(rows) > 1:
        html += "<tbody>\n"
        for row in rows[1:]:
            html += "<tr>\n"
            for cell in row:
                html += '<td style="border:1px solid #ddd;padding:8px;text-align:left;">' + _inline_format(cell) + "</td>\n"
            html += "</tr>\n"
        html += "</tbody>\n"
    html += "</table>\n"
    return html, i


def markdown_to_toutiao_html(markdown_text):
    """将 Markdown 转为头条号兼容的 HTML（支持表格、引用、加粗等）"""
    lines = markdown_text.split("\n")
    html_parts = []
    in_blockquote = False
    in_list = False
    in_ordered_list = False
    i = 0

    while i < len(lines):
        stripped = lines[i].strip()

        # --- Table (multi-line block) ---
        if stripped.startswith("|"):
            if in_blockquote:
                html_parts.append('</blockquote>\n')
                in_blockquote = False
            if in_list:
                html_parts.append('</ul>\n')
                in_list = False
            if in_ordered_list:
                html_parts.append('</ol>\n')
                in_ordered_list = False
            table_html, next_i = _parse_table(lines, i)
            html_parts.append(table_html)
            i = next_i
            continue

        # --- Image ---
        img_match = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)$", stripped)
        if img_match:
            if in_blockquote:
                html_parts.append('</blockquote>\n')
                in_blockquote = False
            if in_list:
                html_parts.append('</ul>\n')
                in_list = False
            if in_ordered_list:
                html_parts.append('</ol>\n')
                in_ordered_list = False
            alt = img_match.group(1)
            src = img_match.group(2)
            html_parts.append(f'<p><img src="{src}" alt="{alt}" style="max-width:100%"></p>\n')
            i += 1
            continue

        # --- Horizontal rule ---
        if stripped.startswith("---") and len(stripped) >= 3:
            if in_blockquote:
                html_parts.append('</blockquote>\n')
                in_blockquote = False
            if in_list:
                html_parts.append('</ul>\n')
                in_list = False
            if in_ordered_list:
                html_parts.append('</ol>\n')
                in_ordered_list = False
            html_parts.append('<hr style="border:none;border-top:1px solid #e0e0e0;margin:20px 0;">\n')
            i += 1
            continue

        # --- Blockquote ---
        if stripped.startswith("> "):
            if in_list:
                html_parts.append('</ul>\n')
                in_list = False
            if in_ordered_list:
                html_parts.append('</ol>\n')
                in_ordered_list = False
            if not in_blockquote:
                html_parts.append('<blockquote style="border-left:4px solid #ddd;margin:12px 0;padding:8px 16px;color:#666;">\n')
                in_blockquote = True
            content = _inline_format(stripped[2:])
            html_parts.append(f"<p>{content}</p>\n")
            i += 1
            continue

        # Close blockquote on non-quote lines
        if in_blockquote:
            html_parts.append('</blockquote>\n')
            in_blockquote = False

        # --- Headers ---
        if stripped.startswith("#### "):
            if in_list:
                html_parts.append('</ul>\n')
                in_list = False
            if in_ordered_list:
                html_parts.append('</ol>\n')
                in_ordered_list = False
            html_parts.append(f"<h4>{_inline_format(stripped[5:])}</h4>\n")
            i += 1
            continue
        elif stripped.startswith("### "):
            if in_list:
                html_parts.append('</ul>\n')
                in_list = False
            if in_ordered_list:
                html_parts.append('</ol>\n')
                in_ordered_list = False
            html_parts.append(f"<h3>{_inline_format(stripped[4:])}</h3>\n")
            i += 1
            continue
        elif stripped.startswith("## "):
            if in_list:
                html_parts.append('</ul>\n')
                in_list = False
            if in_ordered_list:
                html_parts.append('</ol>\n')
                in_ordered_list = False
            html_parts.append(f"<h2>{_inline_format(stripped[3:])}</h2>\n")
            i += 1
            continue
        elif stripped.startswith("# "):
            if in_list:
                html_parts.append('</ul>\n')
                in_list = False
            if in_ordered_list:
                html_parts.append('</ol>\n')
                in_ordered_list = False
            html_parts.append(f"<h1>{_inline_format(stripped[2:])}</h1>\n")
            i += 1
            continue

        # --- Unordered list ---
        if stripped.startswith("- ") or stripped.startswith("* "):
            if in_ordered_list:
                html_parts.append('</ol>\n')
                in_ordered_list = False
            if not in_list:
                html_parts.append('<ul>\n')
                in_list = True
            content = _inline_format(stripped[2:])
            html_parts.append(f"<li>{content}</li>\n")
            i += 1
            continue

        # --- Ordered list ---
        ol_match = re.match(r"^\d+\.\s+(.*)", stripped)
        if ol_match:
            if in_list:
                html_parts.append('</ul>\n')
                in_list = False
            if not in_ordered_list:
                html_parts.append('<ol>\n')
                in_ordered_list = True
            content = _inline_format(ol_match.group(1))
            html_parts.append(f"<li>{content}</li>\n")
            i += 1
            continue

        # --- Close lists on non-list lines ---
        if in_list:
            html_parts.append('</ul>\n')
            in_list = False
        if in_ordered_list:
            html_parts.append('</ol>\n')
            in_ordered_list = False

        # --- Empty line ---
        if not stripped:
            i += 1
            continue

        # --- Regular paragraph ---
        html_parts.append(f"<p>{_inline_format(stripped)}</p>\n")
        i += 1

    # Close any open tags
    if in_blockquote:
        html_parts.append('</blockquote>\n')
    if in_list:
        html_parts.append('</ul>\n')
    if in_ordered_list:
        html_parts.append('</ol>\n')

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
