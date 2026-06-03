#!/usr/bin/env python3
"""
知乎专栏自动发布脚本
通过 zhuanlan.zhihu.com API，使用 cookie + x-zse-96 签名认证

流程: 创建草稿 → 更新内容 → 发布
用法: python3 scripts/publish_zhihu.py <markdown_file>
      cat article.md | python3 scripts/publish_zhihu.py -
"""

import sys
import os
import re
import json
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime

# 添加脚本目录到 path
SCRIPT_DIR = Path(__file__).parent
SITE_DIR = SCRIPT_DIR.parent

sys.path.insert(0, str(SCRIPT_DIR))
from zhihu_zse96 import get_xzse96

COOKIE_FILE = SCRIPT_DIR / ".zhihu_cookie"
BASE_URL = "https://zhuanlan.zhihu.com"

# 知乎外部图床：文章中的图片相对路径会替换为 GitHub raw URL
# markdown 引用图片时用 `images/xxx.jpg`，发布时自动转成完整可访问 URL
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/wk123-11/ai-tool-review/main/"


def load_cookie():
    """从文件加载 cookie, 提取 d_c0 和 z_c0"""
    if not COOKIE_FILE.exists():
        print(f"❌ Cookie file not found: {COOKIE_FILE}")
        sys.exit(1)
    cookie_str = COOKIE_FILE.read_text().strip()

    # 提取各 cookie 值
    cookies = {}
    for part in cookie_str.split(";"):
        part = part.strip()
        if "=" in part:
            key, val = part.split("=", 1)
            cookies[key.strip()] = val.strip()

    d_c0 = cookies.get("d_c0", "")
    z_c0 = cookies.get("z_c0", "")
    _xsrf = cookies.get("_xsrf", "")

    if not d_c0:
        print("❌ d_c0 not found in cookie")
        sys.exit(1)
    if not z_c0:
        print("❌ z_c0 not found in cookie")
        sys.exit(1)

    return cookie_str, d_c0, z_c0, _xsrf


def parse_markdown_post(filepath):
    """解析 Jekyll markdown 文章，提取 frontmatter 和内容"""
    if filepath == "-":
        stdin_data = sys.stdin.read().strip()
        if not stdin_data:
            print("❌ No input from stdin")
            sys.exit(1)
        # 从第一个 # 标题提取
        title = "AI工具派文章"
        body_lines = []
        for line in stdin_data.split("\n"):
            body_lines.append(line)
        body = "\n".join(body_lines)
        # 提取标题
        for line in body_lines:
            s = line.strip()
            if s.startswith("# "):
                title = s[2:].strip()
                break
            elif s.startswith("## "):
                title = s[3:].strip()
                break
        return title, body

    path = Path(filepath)
    if not path.exists():
        print(f"❌ File not found: {filepath}")
        sys.exit(1)

    text = path.read_text(encoding="utf-8")

    # Parse Jekyll frontmatter
    title = ""
    body = text.strip()
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", text, re.DOTALL)
    if match:
        frontmatter = match.group(1)
        body = match.group(2).strip()
        t = re.search(r"title:\s*(.+)", frontmatter)
        if t:
            title = t.group(1).strip().strip('"').strip("'")

    if not title:
        # Fallback: first heading
        for line in body.split("\n"):
            s = line.strip()
            if s.startswith("# "):
                title = s[2:].strip()
                break

    return title, body


def _inline_format(text):
    """行内格式：加粗、斜体、行内代码、链接"""
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', text)
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" rel="nofollow">\1</a>', text)
    return text


def _parse_table(lines, start_idx):
    """解析 markdown 表格，返回 (html, end_idx)"""
    rows = []
    i = start_idx
    while i < len(lines):
        stripped = lines[i].strip()
        if not stripped.startswith("|"):
            break
        if re.match(r"^\|[\s\-:]+\|", stripped):
            i += 1
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        rows.append(cells)
        i += 1

    if not rows:
        return "", start_idx

    html = '<table style="width:100%;border-collapse:collapse;margin:12px 0;font-size:14px;">\n'
    html += "<thead><tr>\n"
    for cell in rows[0]:
        html += '<th style="border:1px solid #ddd;padding:8px;background:#f5f5f5;font-weight:bold;text-align:left;">' + _inline_format(cell) + "</th>\n"
    html += "</tr></thead>\n"
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


def markdown_to_zhihu_html(md_text):
    """Markdown → 知乎兼容 HTML（支持表格、引用、加粗等）"""
    lines = md_text.split("\n")
    html_parts = []
    in_blockquote = False
    in_list = False
    in_ordered_list = False
    i = 0

    while i < len(lines):
        stripped = lines[i].strip()

        # Table (multi-line block)
        if stripped.startswith("|"):
            if in_blockquote: html_parts.append('</blockquote>\n'); in_blockquote = False
            if in_list: html_parts.append('</ul>\n'); in_list = False
            if in_ordered_list: html_parts.append('</ol>\n'); in_ordered_list = False
            table_html, next_i = _parse_table(lines, i)
            html_parts.append(table_html)
            i = next_i
            continue

        # Image
        img_match = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)$", stripped)
        if img_match:
            if in_blockquote: html_parts.append('</blockquote>\n'); in_blockquote = False
            if in_list: html_parts.append('</ul>\n'); in_list = False
            if in_ordered_list: html_parts.append('</ol>\n'); in_ordered_list = False
            alt, src = img_match.group(1), img_match.group(2)
            # 图片相对路径 → GitHub raw URL（避免头条 CDN 裂图）
            if not src.startswith("http"):
                src = GITHUB_RAW_BASE + src
            html_parts.append(f'<p><img src="{src}" alt="{alt}" style="max-width:100%"></p>\n')
            i += 1
            continue

        # Horizontal rule
        if stripped.startswith("---") and len(stripped) >= 3:
            if in_blockquote: html_parts.append('</blockquote>\n'); in_blockquote = False
            if in_list: html_parts.append('</ul>\n'); in_list = False
            if in_ordered_list: html_parts.append('</ol>\n'); in_ordered_list = False
            html_parts.append('<hr style="border:none;border-top:1px solid #e0e0e0;margin:20px 0;">\n')
            i += 1
            continue

        # Blockquote
        if stripped.startswith("> "):
            if in_list: html_parts.append('</ul>\n'); in_list = False
            if in_ordered_list: html_parts.append('</ol>\n'); in_ordered_list = False
            if not in_blockquote:
                html_parts.append('<blockquote style="border-left:4px solid #ddd;margin:12px 0;padding:8px 16px;color:#666;">\n')
                in_blockquote = True
            html_parts.append(f"<p>{_inline_format(stripped[2:])}</p>\n")
            i += 1
            continue

        if in_blockquote:
            html_parts.append('</blockquote>\n')
            in_blockquote = False

        # Headers
        if stripped.startswith("#### "):
            if in_list: html_parts.append('</ul>\n'); in_list = False
            if in_ordered_list: html_parts.append('</ol>\n'); in_ordered_list = False
            html_parts.append(f"<h4>{_inline_format(stripped[5:])}</h4>\n")
            i += 1; continue
        elif stripped.startswith("### "):
            if in_list: html_parts.append('</ul>\n'); in_list = False
            if in_ordered_list: html_parts.append('</ol>\n'); in_ordered_list = False
            html_parts.append(f"<h3>{_inline_format(stripped[4:])}</h3>\n")
            i += 1; continue
        elif stripped.startswith("## "):
            if in_list: html_parts.append('</ul>\n'); in_list = False
            if in_ordered_list: html_parts.append('</ol>\n'); in_ordered_list = False
            html_parts.append(f"<h2>{_inline_format(stripped[3:])}</h2>\n")
            i += 1; continue

        # Unordered list
        if stripped.startswith("- ") or stripped.startswith("* "):
            if in_ordered_list: html_parts.append('</ol>\n'); in_ordered_list = False
            if not in_list: html_parts.append('<ul>\n'); in_list = True
            html_parts.append(f"<li>{_inline_format(stripped[2:])}</li>\n")
            i += 1; continue

        # Ordered list
        ol_match = re.match(r"^\d+\.\s+(.*)", stripped)
        if ol_match:
            if in_list: html_parts.append('</ul>\n'); in_list = False
            if not in_ordered_list: html_parts.append('<ol>\n'); in_ordered_list = True
            html_parts.append(f"<li>{_inline_format(ol_match.group(1))}</li>\n")
            i += 1; continue

        if in_list: html_parts.append('</ul>\n'); in_list = False
        if in_ordered_list: html_parts.append('</ol>\n'); in_ordered_list = False

        if not stripped:
            i += 1; continue

        html_parts.append(f"<p>{_inline_format(stripped)}</p>\n")
        i += 1

    if in_blockquote: html_parts.append('</blockquote>\n')
    if in_list: html_parts.append('</ul>\n')
    if in_ordered_list: html_parts.append('</ol>\n')

    return "".join(html_parts)


def mkheaders(cookie_str, xsrf, api_path, d_c0):
    """构造请求头, 自动生成 x-zse-96 签名"""
    sig = get_xzse96(d_c0, api_path)
    return {
        "Cookie": cookie_str,
        "x-zse-93": "101_3_3.0",
        "x-zse-96": sig,
        "x-requested-with": "fetch",
        "Referer": "https://zhuanlan.zhihu.com/",
        "Origin": "https://zhuanlan.zhihu.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0",
        "Content-Type": "application/json;charset=UTF-8",
        "Accept": "application/json, text/plain, */*",
    }


def api_request(method, api_path, cookie_str, d_c0, xsrf, body=None):
    """发送 API 请求, 自动签名"""
    url = f"{BASE_URL}{api_path}"
    headers = mkheaders(cookie_str, xsrf, api_path, d_c0)

    data = None
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
            if not raw:
                return {}, resp.status
            result = json.loads(raw.decode("utf-8"))
            return result, resp.status
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")[:500]
        print(f"❌ HTTP {e.code}: {err_body}")
        return {"error": str(e)}, e.code
    except urllib.error.URLError as e:
        print(f"❌ Network error: {e.reason}")
        return {"error": str(e)}, 0


def publish_post(title, html_content, cookie_str, d_c0, z_c0, xsrf):
    """三阶段发布流程"""

    # ---- 阶段 1: 创建草稿 ----
    print("📝 阶段 1/3: 创建草稿...")
    draft_body = {
        "title": title,
        "content": html_content,
    }
    result, status = api_request(
        "POST", "/api/articles/drafts",
        cookie_str, d_c0, xsrf, draft_body
    )
    if status != 200:
        print(f"❌ 创建草稿失败 (status={status})")
        return False, None

    if not isinstance(result, dict):
        print(f"❌ 草稿返回格式异常: {str(result)[:200]}")
        return False, None

    article_id = None
    if "id" in result:
        article_id = result["id"]
    elif "article" in result:
        article_id = result["article"].get("id")
    elif "data" in result:
        article_id = result["data"].get("id")

    if not article_id:
        print(f"❌ 无法获取文章 ID, response: {json.dumps(result, ensure_ascii=False)[:300]}")
        return False, None

    print(f"   ✅ 草稿创建成功, 文章 ID: {article_id}")

    # ---- 阶段 2: 更新内容 (PATCH draft) ----
    print("📝 阶段 2/3: 更新草稿内容...")
    update_body = {
        "title": title,
        "content": html_content,
    }
    result2, status2 = api_request(
        "PATCH", f"/api/articles/{article_id}/draft",
        cookie_str, d_c0, xsrf, update_body
    )
    if status2 != 200:
        print(f"⚠️  PATCH 草稿返回 {status2}, 尝试继续发布...")
    else:
        print("   ✅ 草稿内容已更新")

    # ---- 阶段 3: 发布 ----
    print("📝 阶段 3/3: 发布文章...")
    result3, status3 = api_request(
        "PUT", f"/api/articles/{article_id}/publish",
        cookie_str, d_c0, xsrf, {}
    )
    if status3 == 200:
        url = f"https://zhuanlan.zhihu.com/p/{article_id}"
        print(f"✅ 知乎发布成功!")
        print(f"   title: {title}")
        print(f"   url: {url}")
        return True, article_id
    else:
        print(f"❌ 发布失败 (status={status3})")
        return False, article_id


def main():
    if len(sys.argv) < 2:
        print("用法: python3 scripts/publish_zhihu.py <markdown_file>")
        print("      cat article.md | python3 scripts/publish_zhihu.py -")
        sys.exit(1)

    filepath = sys.argv[1]
    title, body = parse_markdown_post(filepath)

    if not title:
        print("❌ Could not extract title")
        sys.exit(1)

    print(f"📝 准备发布到知乎: {title}")

    # Load cookie
    cookie_str, d_c0, z_c0, xsrf = load_cookie()
    print(f"   d_c0: {d_c0[:20]}... (len={len(d_c0)})")
    print(f"   z_c0: {z_c0[:20]}... (len={len(z_c0)})")

    # Convert
    html_content = markdown_to_zhihu_html(body)
    word_count = len(re.sub(r"<[^>]+>", "", html_content))
    print(f"   字数: {word_count}")

    # Publish
    success, article_id = publish_post(title, html_content, cookie_str, d_c0, z_c0, xsrf)

    if success:
        log_path = SCRIPT_DIR / ".zhihu_published_ids"
        with open(log_path, "a") as f:
            f.write(f"{datetime.now().isoformat()}|{article_id}|{title}\n")


if __name__ == "__main__":
    main()
