#!/usr/bin/env python3
"""Create a Zhihu draft or publish an article. Default is dry-run."""
from pathlib import Path
import argparse,json,sys,urllib.error,urllib.request
from content_core import build_preview_document, read_article, render_markdown, strip_leading_h1
from publish_state import AlreadyPublishedError, assert_publishable, get_record, record
from secrets_config import PROJECT_ROOT, SecretConfigError, github_raw_base, load_zhihu_cookie
from zhihu_zse96 import get_xzse96
BASE_URL='https://zhuanlan.zhihu.com'
def parse_cookie(cookie):
    values={}
    for part in cookie.split(';'):
        if '=' in part:
            k,v=part.strip().split('=',1); values[k]=v
    d_c0,z_c0,xsrf=values.get('d_c0',''),values.get('z_c0',''),values.get('_xsrf','')
    if not d_c0 or not z_c0: raise SecretConfigError('Zhihu cookie must contain d_c0 and z_c0')
    return d_c0,z_c0,xsrf
def image_resolver(src): return src if src.startswith(('http://','https://','data:')) else github_raw_base()+src.lstrip('/')
def request(method,api_path,cookie,d_c0,body=None):
    h={'Cookie':cookie,'x-zse-93':'101_3_3.0','x-zse-96':get_xzse96(d_c0,api_path),'x-requested-with':'fetch','Referer':'https://zhuanlan.zhihu.com/','Origin':'https://zhuanlan.zhihu.com','User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/148 Safari/537.36','Content-Type':'application/json;charset=UTF-8','Accept':'application/json, text/plain, */*'}
    data=json.dumps(body,ensure_ascii=False).encode('utf-8') if body is not None else None; req=urllib.request.Request(BASE_URL+api_path,data=data,headers=h,method=method)
    try:
        with urllib.request.urlopen(req,timeout=30) as resp:
            raw=resp.read(); return (json.loads(raw.decode('utf-8')) if raw else {}),resp.status
    except urllib.error.HTTPError as e: raise RuntimeError(f'Zhihu HTTP {e.code}: {e.read().decode("utf-8",errors="replace")[:500]}') from e
    except urllib.error.URLError as e: raise RuntimeError(f'Zhihu network error: {e.reason}') from e
def create_draft(title,html,cookie,d_c0):
    result,status=request('POST','/api/articles/drafts',cookie,d_c0,{'title':title,'content':html})
    if status!=200: raise RuntimeError(f'Zhihu draft creation failed: HTTP {status}')
    article_id=result.get('id') or (result.get('article') or {}).get('id') or (result.get('data') or {}).get('id')
    if not article_id: raise RuntimeError(f'Zhihu returned no article ID: {str(result)[:300]}')
    _,status2=request('PATCH',f'/api/articles/{article_id}/draft',cookie,d_c0,{'title':title,'content':html})
    if status2!=200: raise RuntimeError(f'Zhihu draft update failed: HTTP {status2}')
    return str(article_id)
def publish_draft(article_id,cookie,d_c0):
    _,status=request('PUT',f'/api/articles/{article_id}/publish',cookie,d_c0,{})
    if status!=200: raise RuntimeError(f'Zhihu publish failed: HTTP {status}')
def main()->int:
    p=argparse.ArgumentParser(); p.add_argument('markdown_file'); mode=p.add_mutually_exclusive_group(); mode.add_argument('--draft-only',action='store_true'); mode.add_argument('--publish',action='store_true'); p.add_argument('--force',action='store_true'); p.add_argument('--preview'); a=p.parse_args()
    article=read_article(a.markdown_file,sys.stdin.read() if a.markdown_file=='-' else None); body=strip_leading_h1(article.body); html=render_markdown(body,image_resolver)
    out=Path(a.preview) if a.preview else PROJECT_ROOT/'preview'/f'{article.content_id}-zhihu.html'; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(build_preview_document(article.title,html,'zhihu'),encoding='utf-8'); print(f'Preview: {out}')
    if not a.draft_only and not a.publish: print('Dry-run only. Add --draft-only or --publish after review.'); return 0
    try:
        existing=get_record('zhihu',article.content_id)
        cookie=load_zhihu_cookie(); d_c0,_,_=parse_cookie(cookie)
        if a.publish and existing and existing.get('status')=='draft' and not a.force:
            article_id=str(existing.get('remote_id',''))
            if not article_id: raise RuntimeError('recorded Zhihu draft has no article ID')
            publish_draft(article_id,cookie,d_c0)
            url=f'https://zhuanlan.zhihu.com/p/{article_id}'; record('zhihu',article.content_id,article.title,'published',remote_id=article_id,url=url); print(f'Published existing Zhihu draft: {url}'); return 0
        assert_publishable('zhihu',article.content_id,article.title,force=a.force)
        article_id=create_draft(article.title,html,cookie,d_c0)
        if a.publish:
            publish_draft(article_id,cookie,d_c0); url=f'https://zhuanlan.zhihu.com/p/{article_id}'; record('zhihu',article.content_id,article.title,'published',remote_id=article_id,url=url); print(f'Published to Zhihu: {url}')
        else: record('zhihu',article.content_id,article.title,'draft',remote_id=article_id); print(f'Zhihu draft created: {article_id}')
        return 0
    except (AlreadyPublishedError,SecretConfigError,RuntimeError) as e: print(f'ERROR: {e}',file=sys.stderr); return 1
if __name__=='__main__': raise SystemExit(main())
