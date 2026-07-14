#!/usr/bin/env python3
"""Create offline platform previews without network calls."""
from pathlib import Path
import argparse, sys
from content_core import build_preview_document, local_image_to_data_url, read_article, render_markdown, strip_leading_h1
from secrets_config import PROJECT_ROOT, github_raw_base

def main() -> int:
    p=argparse.ArgumentParser(); p.add_argument('markdown_file'); p.add_argument('--platform',choices=['toutiao','zhihu','github'],default='toutiao'); p.add_argument('--output'); a=p.parse_args()
    article=read_article(a.markdown_file,sys.stdin.read() if a.markdown_file=='-' else None); body=strip_leading_h1(article.body)
    if a.platform=='zhihu':
        def resolver(src): return src if src.startswith(('http://','https://','data:')) else github_raw_base()+src.lstrip('/')
    else: resolver=lambda src: local_image_to_data_url(PROJECT_ROOT,src)
    rendered=render_markdown(body,resolver,first_paragraph_track=a.platform=='toutiao')
    out=Path(a.output) if a.output else PROJECT_ROOT/'preview'/f'{article.content_id}-{a.platform}.html'; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(build_preview_document(article.title,rendered,a.platform),encoding='utf-8'); print(out); return 0
if __name__=='__main__': raise SystemExit(main())
