import base64, re, os, sys

with open("_posts/2026-06-01-ai-coding-assistants-comparison.md", "r") as f:
    content = f.read()

# Strip YAML frontmatter
content = re.sub(r'^---\n.*?\n---\n', '', content, flags=re.DOTALL)

def inline_convert(text):
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
    text = re.sub(r'!\[(.*?)\]\((/images/[^)]+)\)', lambda m: f'<img src="{m.group(2)}" alt="{m.group(1)}" style="max-width:100%">', text)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank" rel="noopener">\1</a>', text)
    return text

def md_to_html(text):
    lines = text.split('\n')
    html = []
    i = 0
    in_table = False
    in_list = False
    list_type = None
    
    while i < len(lines):
        line = lines[i]
        if line.startswith('### '):
            html.append(f'<h3>{inline_convert(line[4:])}</h3>')
        elif line.startswith('## '):
            html.append(f'<h2>{inline_convert(line[3:])}</h2>')
        elif line.startswith('# '):
            html.append(f'<h1>{inline_convert(line[2:])}</h1>')
        elif line == '---':
            html.append('<hr>')
        elif line.startswith('> '):
            html.append(f'<blockquote><p>{inline_convert(line[2:])}</p></blockquote>')
        elif '|' in line and line.strip().startswith('|'):
            if not in_table:
                html.append('<table>')
                in_table = True
            if re.match(r'^\|[\s\-:|]+\|$', line):
                i += 1
                continue
            cells = [c.strip() for c in line.strip().split('|')[1:-1]]
            is_header = False
            if i + 1 < len(lines) and re.match(r'^\|[\s\-:|]+\|$', lines[i+1]):
                is_header = True
            if is_header:
                html.append(f'<thead><tr>{"".join(f"<th>{inline_convert(c)}</th>" for c in cells)}</tr></thead><tbody>')
            else:
                html.append(f'<tr>{"".join(f"<td>{inline_convert(c)}</td>" for c in cells)}</tr>')
        else:
            if in_table:
                html.append('</tbody></table>')
                in_table = False
            if line.lstrip().startswith('- '):
                item = inline_convert(line.lstrip()[2:])
                if not in_list:
                    html.append('<ul>')
                    in_list = True
                html.append(f'<li>{item}</li>')
            elif re.match(r'^\s*\d+\.\s', line):
                item = inline_convert(re.sub(r'^\s*\d+\.\s', '', line))
                if not in_list:
                    html.append('<ol>')
                    in_list = True
                    list_type = 'ol'
                html.append(f'<li>{item}</li>')
            elif line.strip() == '':
                if in_list:
                    html.append(f'</{"ol" if list_type else "ul"}>')
                    in_list = False
                    list_type = None
            elif line.strip():
                html.append(f'<p>{inline_convert(line)}</p>')
        i += 1
    
    if in_table:
        html.append('</tbody></table>')
    if in_list:
        html.append(f'</{"ol" if list_type else "ul"}>')
    return '\n'.join(html)

html_body = md_to_html(content)

def embed(m):
    src = m.group(1)
    alt = m.group(2)
    path = src.lstrip('/')
    if os.path.exists(path):
        with open(path, 'rb') as f:
            b64 = base64.b64encode(f.read()).decode()
        ext = os.path.splitext(path)[1][1:]
        if ext == 'jpg': ext = 'jpeg'
        return f'<img src="data:image/{ext};base64,{b64}" alt="{alt}">'
    return f'<img src="{src}" alt="{alt}">'

html_body = re.sub(r'<img\s+src="([^"]*)"\s+alt="([^"]*)"[^>]*>', embed, html_body)

html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>预览：AI编程助手横评 2026</title>
<style>
body{{font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;max-width:820px;margin:0 auto;padding:24px;color:#333;line-height:1.8;background:#f5f5f5}}
article{{background:#fff;padding:40px 48px;border-radius:12px;box-shadow:0 2px 16px rgba(0,0,0,.08)}}
h1{{font-size:26px;border-left:4px solid #2563eb;padding-left:16px;margin-bottom:24px;color:#111}}
h2{{font-size:22px;margin-top:36px;padding-bottom:10px;border-bottom:2px solid #e5e7eb;color:#1a1a1a}}
h3{{font-size:18px;margin-top:28px;color:#333}}
table{{width:100%;border-collapse:collapse;margin:20px 0;font-size:14px}}
th{{background:#2563eb;color:#fff;padding:10px 12px;border:1px solid #2563eb;text-align:center}}
td{{padding:10px 12px;border:1px solid #ddd;text-align:center}}
tr:nth-child(even){{background:#f8faff}}
blockquote{{border-left:4px solid #2563eb;margin:16px 0;padding:12px 20px;background:#f0f6ff;color:#444;border-radius:0 6px 6px 0}}
code{{background:#f0f0f0;padding:2px 6px;border-radius:4px;font-size:14px;color:#d63384}}
img{{max-width:100%;border-radius:10px;margin:20px 0;box-shadow:0 4px 12px rgba(0,0,0,.12)}}
hr{{border:none;border-top:1px solid #e5e7eb;margin:36px 0}}
p{{margin:12px 0}}
li{{margin:4px 0}}
a{{color:#2563eb;text-decoration:none}}
a:hover{{text-decoration:underline}}
</style></head>
<body><article>
{html_body}
</article></body></html>'''

with open("preview-2026-06-01.html", "w") as f:
    f.write(html)
print(f"✅ 预览已生成: preview-2026-06-01.html ({len(html.encode())} bytes)")
