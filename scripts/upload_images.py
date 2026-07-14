#!/usr/bin/env python3
"""Upload local images to Toutiao CDN and publish. Default is dry-run."""
from pathlib import Path
import argparse,re,sys
from content_core import build_preview_document, local_image_to_data_url, read_article, render_markdown, strip_leading_h1
from publish_state import AlreadyPublishedError, assert_publishable, record
from secrets_config import PROJECT_ROOT, SecretConfigError, github_raw_base, load_toutiao_cookie
from toutiao_api import publish_article, upload_image
IMAGE_RE=re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')
def image_filename(src):
    if src.startswith('/images/'): return src.split('/images/',1)[1].split('?',1)[0]
    raw=github_raw_base()
    if src.startswith(raw+'images/'): return src[len(raw+'images/'):].split('?',1)[0]
    return None
def main()->int:
    p=argparse.ArgumentParser(); p.add_argument('markdown_file'); p.add_argument('--publish',action='store_true'); p.add_argument('--force',action='store_true'); p.add_argument('--preview'); a=p.parse_args()
    article=read_article(a.markdown_file,sys.stdin.read() if a.markdown_file=='-' else None); body=strip_leading_h1(article.body)
    preview_html=render_markdown(body,lambda src: local_image_to_data_url(PROJECT_ROOT,src),first_paragraph_track=True)
    out=Path(a.preview) if a.preview else PROJECT_ROOT/'preview'/f'{article.content_id}-toutiao.html'; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(build_preview_document(article.title,preview_html,'toutiao'),encoding='utf-8'); print(f'Preview: {out}')
    if not a.publish: print('Dry-run only. No image uploaded and no article published.'); return 0
    try:
        assert_publishable('toutiao',article.content_id,article.title,force=a.force); cookie=load_toutiao_cookie(); filenames=sorted({name for _,src in IMAGE_RE.findall(body) if (name:=image_filename(src))}); uploaded={}
        for name in filenames: print(f'Uploading: {name}'); uploaded[name]=upload_image(PROJECT_ROOT/'images'/name,cookie)
        def resolver(src):
            name=image_filename(src)
            if name:
                if name not in uploaded: raise RuntimeError(f'local image was not uploaded: {name}')
                return uploaded[name]
            if src.startswith(('https://image-tt-private.toutiao.com/', 'https://p3-sign.toutiaoimg.com/')):
                return src
            if src.startswith(('http://', 'https://')):
                raise RuntimeError(f'external image is not on Toutiao CDN: {src}')
            raise RuntimeError(f'unsupported image path: {src}')
        html=render_markdown(body,resolver,first_paragraph_track=True); remote=publish_article(article.title,html,cookie); record('toutiao',article.content_id,article.title,'published',remote_id=remote); print(f'Published to Toutiao: {remote}'); return 0
    except (AlreadyPublishedError,SecretConfigError,RuntimeError,FileNotFoundError,ValueError) as e: print(f'ERROR: {e}',file=sys.stderr); return 1
if __name__=='__main__': raise SystemExit(main())
