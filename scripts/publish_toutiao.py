#!/usr/bin/env python3
"""Render and optionally publish a text-only Toutiao article. Default is dry-run."""
from pathlib import Path
import argparse,re,sys
from content_core import build_preview_document, local_image_to_data_url, read_article, render_markdown, strip_leading_h1
from publish_state import AlreadyPublishedError, assert_publishable, record
from secrets_config import PROJECT_ROOT, SecretConfigError, load_toutiao_cookie
from toutiao_api import publish_article
IMAGE_RE=re.compile(r'!\[[^\]]*\]\(([^)]+)\)')
def main()->int:
    p=argparse.ArgumentParser(); p.add_argument('markdown_file'); p.add_argument('--publish',action='store_true'); p.add_argument('--force',action='store_true'); p.add_argument('--preview'); a=p.parse_args()
    article=read_article(a.markdown_file,sys.stdin.read() if a.markdown_file=='-' else None); body=strip_leading_h1(article.body)
    rendered=render_markdown(body,lambda src: local_image_to_data_url(PROJECT_ROOT,src),first_paragraph_track=True)
    out=Path(a.preview) if a.preview else PROJECT_ROOT/'preview'/f'{article.content_id}-toutiao.html'; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(build_preview_document(article.title,rendered,'toutiao'),encoding='utf-8'); print(f'Preview: {out}')
    if not a.publish: print('Dry-run only. Add --publish after reviewing the preview.'); return 0
    if IMAGE_RE.search(body): print('Images detected. Use upload_images.py --publish so Toutiao CDN rules are enforced.',file=sys.stderr); return 2
    try:
        assert_publishable('toutiao',article.content_id,article.title,force=a.force); cookie=load_toutiao_cookie(); html=render_markdown(body,first_paragraph_track=True); remote=publish_article(article.title,html,cookie); record('toutiao',article.content_id,article.title,'published',remote_id=remote); print(f'Published to Toutiao: {remote}'); return 0
    except (AlreadyPublishedError,SecretConfigError,RuntimeError) as e: print(f'ERROR: {e}',file=sys.stderr); return 1
if __name__=='__main__': raise SystemExit(main())
