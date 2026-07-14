#!/usr/bin/env python3
"""Shared article parsing and Markdown rendering utilities."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional
import base64
import hashlib
import html
import mimetypes
import re

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)

@dataclass(frozen=True)
class Article:
    source: Optional[Path]
    frontmatter: dict[str, str]
    title: str
    body: str
    content_id: str

def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value

def parse_frontmatter(raw: str) -> dict[str, str]:
    data: dict[str, str] = {}
    for original in raw.splitlines():
        line = original.strip()
        if not line or line.startswith('#') or ':' not in line:
            continue
        if line.startswith('|layout:'):
            line = line[1:]
        key, value = line.split(':', 1)
        key = key.strip()
        if key and re.fullmatch(r'[A-Za-z0-9_-]+', key):
            data[key] = _unquote(value)
    return data

def stable_content_id(path: Optional[Path], title: str, body: str, explicit: str = '') -> str:
    if explicit:
        return explicit.strip()
    if path:
        return 'atr-' + path.stem
    digest = hashlib.sha256((title + '\n' + body).encode('utf-8')).hexdigest()[:16]
    return f'atr-stdin-{digest}'

def read_article(source: str | Path, stdin_text: str | None = None) -> Article:
    if str(source) == '-':
        if not stdin_text or not stdin_text.strip():
            raise ValueError('stdin is empty')
        text, path = stdin_text.strip(), None
    else:
        path = Path(source).resolve()
        if not path.exists():
            raise FileNotFoundError(path)
        text = path.read_text(encoding='utf-8')
    match = FRONTMATTER_RE.match(text)
    if match:
        fm, body = parse_frontmatter(match.group(1)), match.group(2).strip()
    else:
        fm, body = {}, text.strip()
    title = fm.get('title', '').strip()
    if not title:
        for line in body.splitlines():
            if line.strip().startswith('# '):
                title = line.strip()[2:].strip()
                break
    if not title:
        raise ValueError('could not extract article title')
    return Article(path, fm, title, body, stable_content_id(path, title, body, fm.get('content_id', '')))

def strip_leading_h1(body: str) -> str:
    lines = body.splitlines()
    for idx, line in enumerate(lines):
        if not line.strip():
            continue
        if line.strip().startswith('# '):
            del lines[idx]
            while idx < len(lines) and not lines[idx].strip():
                del lines[idx]
        break
    return '\n'.join(lines).strip()

def _inline_format(text: str) -> str:
    tokens: dict[str, str] = {}
    def reserve(rendered: str) -> str:
        key = f'@@TOKEN{len(tokens)}@@'
        tokens[key] = rendered
        return key
    text = re.sub(r'`([^`]+)`', lambda m: reserve(f'<code>{html.escape(m.group(1), quote=False)}</code>'), text)
    text = re.sub(
        r'\[([^\]]+)\]\(([^)]+)\)',
        lambda m: reserve(f'<a href="{html.escape(m.group(2).strip(), quote=True)}" rel="nofollow noopener">{html.escape(m.group(1), quote=False)}</a>'),
        text,
    )
    text = html.escape(text, quote=False)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', text)
    for key, value in tokens.items():
        text = text.replace(key, value)
    return text

def _is_separator_row(line: str) -> bool:
    cells = [cell.strip() for cell in line.strip().strip('|').split('|')]
    return bool(cells) and all(re.fullmatch(r':?-{3,}:?', cell or '') for cell in cells)

def _parse_table(lines: list[str], start: int) -> tuple[str, int]:
    raw_rows: list[list[str]] = []
    i = start
    while i < len(lines) and lines[i].strip().startswith('|'):
        stripped = lines[i].strip()
        if not _is_separator_row(stripped):
            raw_rows.append([cell.strip() for cell in stripped.strip('|').split('|')])
        i += 1
    if not raw_rows:
        return '', start + 1
    width = max(len(row) for row in raw_rows)
    rows = [row + [''] * (width - len(row)) for row in raw_rows]
    parts = ['<div class="table-scroll" style="max-width:100%;overflow-x:auto;margin:16px 0;"><table style="width:100%;border-collapse:collapse;font-size:14px;"><thead><tr>']
    parts.extend(f'<th style="border:1px solid #ddd;padding:8px;background:#f5f5f5;text-align:left;">{_inline_format(cell)}</th>' for cell in rows[0])
    parts.append('</tr></thead>')
    if len(rows) > 1:
        parts.append('<tbody>')
        for row in rows[1:]:
            parts.append('<tr>')
            parts.extend(f'<td style="border:1px solid #ddd;padding:8px;text-align:left;vertical-align:top;">{_inline_format(cell)}</td>' for cell in row)
            parts.append('</tr>')
        parts.append('</tbody>')
    parts.append('</table></div>')
    return ''.join(parts), i

ImageResolver = Callable[[str], str]

def render_markdown(markdown_text: str, image_resolver: ImageResolver | None = None, *, include_h1: bool = False, first_paragraph_track: bool = False) -> str:
    lines, out = markdown_text.splitlines(), []
    in_ul = in_ol = in_quote = False
    first_p = True
    def close_blocks() -> None:
        nonlocal in_ul, in_ol, in_quote
        if in_quote: out.append('</blockquote>'); in_quote = False
        if in_ul: out.append('</ul>'); in_ul = False
        if in_ol: out.append('</ol>'); in_ol = False
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        if stripped.startswith('|') and i + 1 < len(lines) and _is_separator_row(lines[i + 1].strip()):
            close_blocks(); table, i = _parse_table(lines, i); out.append(table); continue
        image_match = re.fullmatch(r'!\[([^\]]*)\]\(([^)]+)\)', stripped)
        if image_match:
            close_blocks(); alt, src = image_match.group(1), image_match.group(2).strip()
            if image_resolver: src = image_resolver(src)
            out.append(f'<p style="text-align:center;"><img src="{html.escape(src, quote=True)}" alt="{html.escape(alt, quote=True)}" style="max-width:100%;height:auto;"></p>');
            if alt: out.append(f'<p style="text-align:center;color:#888;font-size:13px;">{html.escape(alt)}</p>')
            i += 1; continue
        if re.fullmatch(r'-{3,}', stripped):
            close_blocks(); out.append('<hr>'); i += 1; continue
        if stripped.startswith('>'):
            if in_ul: out.append('</ul>'); in_ul = False
            if in_ol: out.append('</ol>'); in_ol = False
            if not in_quote: out.append('<blockquote style="border-left:4px solid #ddd;margin:12px 0;padding:8px 16px;color:#666;">'); in_quote = True
            out.append(f'<p>{_inline_format(stripped[1:].lstrip())}</p>'); i += 1; continue
        elif in_quote:
            out.append('</blockquote>'); in_quote = False
        heading = re.match(r'^(#{1,4})\s+(.+)$', stripped)
        if heading:
            close_blocks(); level = len(heading.group(1))
            if level != 1 or include_h1: out.append(f'<h{level}>{_inline_format(heading.group(2))}</h{level}>')
            i += 1; continue
        if stripped.startswith(('- ', '* ')):
            if in_ol: out.append('</ol>'); in_ol = False
            if not in_ul: out.append('<ul>'); in_ul = True
            out.append(f'<li>{_inline_format(stripped[2:])}</li>'); i += 1; continue
        ordered = re.match(r'^\d+\.\s+(.+)$', stripped)
        if ordered:
            if in_ul: out.append('</ul>'); in_ul = False
            if not in_ol: out.append('<ol>'); in_ol = True
            out.append(f'<li>{_inline_format(ordered.group(1))}</li>'); i += 1; continue
        if in_ul: out.append('</ul>'); in_ul = False
        if in_ol: out.append('</ol>'); in_ol = False
        if not stripped: i += 1; continue
        attr = ' data-track="1"' if first_p and first_paragraph_track else ''
        out.append(f'<p{attr}>{_inline_format(stripped)}</p>'); first_p = False; i += 1
    close_blocks()
    return '\n'.join(out)

def local_image_to_data_url(project_root: Path, src: str) -> str:
    if src.startswith(('http://', 'https://', 'data:')):
        return src
    path = project_root / src.lstrip('/')
    if not path.exists() or not path.is_file():
        return src
    mime = mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
    return f'data:{mime};base64,{base64.b64encode(path.read_bytes()).decode("ascii")}'

def build_preview_document(title: str, article_html: str, platform: str) -> str:
    safe_title = html.escape(title)
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{safe_title} - {html.escape(platform)}预览</title><style>
*{{box-sizing:border-box}}body{{margin:0;background:#f3f4f6;color:#222;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;line-height:1.8}}article{{max-width:760px;margin:24px auto;padding:32px 36px;background:#fff;border-radius:10px;box-shadow:0 2px 14px rgba(0,0,0,.07)}}h1{{font-size:26px;line-height:1.35;margin:0 0 24px}}h2{{font-size:21px;margin:34px 0 14px}}h3{{font-size:18px;margin:28px 0 12px}}h4{{font-size:16px;margin:24px 0 10px}}p{{margin:12px 0}}ul,ol{{padding-left:26px}}li{{margin:5px 0}}blockquote{{margin:18px 0;padding:10px 16px;border-left:4px solid #64748b;background:#f8fafc;color:#475569}}figure{{margin:22px 0}}img{{max-width:100%;height:auto;display:block;margin:auto;border-radius:7px}}figcaption{{font-size:13px;color:#777;text-align:center;margin-top:7px}}.table-scroll{{max-width:100%;overflow-x:auto;margin:20px 0}}table{{border-collapse:collapse;min-width:620px;width:100%;font-size:14px}}th,td{{border:1px solid #ddd;padding:9px 10px;text-align:left;vertical-align:top}}th{{background:#f4f6f8}}code{{background:#f1f5f9;padding:2px 5px;border-radius:4px}}hr{{border:0;border-top:1px solid #e5e7eb;margin:30px 0}}@media(max-width:640px){{article{{margin:0;padding:22px 18px;border-radius:0}}h1{{font-size:23px}}h2{{font-size:19px}}}}
</style></head><body><article><h1>{safe_title}</h1>{article_html}</article></body></html>'''
