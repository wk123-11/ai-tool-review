#!/usr/bin/env python3
"""Low-level Toutiao upload and publish API helpers."""
from pathlib import Path
import io,json,mimetypes,re,urllib.error,urllib.parse,urllib.request,uuid
USER_AGENT='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/148 Safari/537.36'
REFERER='https://mp.toutiao.com/profile_v4/graphic/publish'
def headers(cookie): return {'Cookie':cookie,'User-Agent':USER_AGENT,'Origin':'https://mp.toutiao.com','Referer':REFERER}
def _csrf(cookie):
    m=re.search(r'(?:^|;\s*)passport_csrf_token=([^;]+)',cookie); return m.group(1) if m else ''
def _multipart(filename,filedata,content_type):
    boundary='----WebKitFormBoundary'+uuid.uuid4().hex[:16]; body=io.BytesIO()
    body.write(f'--{boundary}\r\n'.encode()); body.write(f'Content-Disposition: form-data; name="image"; filename="{filename}"\r\n'.encode()); body.write(f'Content-Type: {content_type}\r\n\r\n'.encode()); body.write(filedata); body.write(f'\r\n--{boundary}--\r\n'.encode())
    return body.getvalue(),f'multipart/form-data; boundary={boundary}'
def upload_image(path: Path,cookie: str)->str:
    if not path.exists(): raise FileNotFoundError(path)
    if path.stat().st_size<100: raise ValueError(f'image appears invalid: {path}')
    body,ctype=_multipart(path.name,path.read_bytes(),mimetypes.guess_type(path.name)[0] or 'image/jpeg')
    h=headers(cookie); h.update({'Content-Type':ctype,'x-secsdk-csrf-token':_csrf(cookie)})
    req=urllib.request.Request('https://mp.toutiao.com/spice/image?upload_source=20020002&aid=1231&device_platform=web',data=body,headers=h,method='POST')
    try:
        with urllib.request.urlopen(req,timeout=30) as resp: result=json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e: raise RuntimeError(f'Toutiao image upload HTTP {e.code}: {e.read().decode("utf-8",errors="replace")[:300]}') from e
    if result.get('code')!=0: raise RuntimeError(f'Toutiao image upload failed: {result.get("message",result)}')
    url=(result.get('data') or {}).get('image_url') or (result.get('data') or {}).get('url')
    if not url: raise RuntimeError('Toutiao image upload returned no URL')
    return url
def publish_article(title,html_content,cookie)->str:
    endpoint='https://mp.toutiao.com/mp/agw/article/publish?source=mp&type=article&aid=1231'; word_count=len(re.sub(r'<[^>]+>','',html_content))
    form=urllib.parse.urlencode({'content':html_content,'title':title,'article_type':'0','save':'1','source':'29','extra':json.dumps({'content_source':100000000402,'content_word_cnt':word_count,'is_multi_title':0,'sub_titles':[],'gd_ext':{'entrance':'','from_page':'publisher_mp','enter_from':'PC','device_platform':'mp','is_message':0},'tuwen_wtt_trans_flag':'0'},ensure_ascii=False)}).encode('utf-8')
    h=headers(cookie); h.update({'Content-Type':'application/x-www-form-urlencoded;charset=UTF-8','Accept':'application/json, text/plain, */*'})
    req=urllib.request.Request(endpoint,data=form,headers=h,method='POST')
    try:
        with urllib.request.urlopen(req,timeout=30) as resp: result=json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e: raise RuntimeError(f'Toutiao publish HTTP {e.code}: {e.read().decode("utf-8",errors="replace")[:300]}') from e
    if result.get('code')!=0: raise RuntimeError(f'Toutiao publish failed: {result.get("message",result.get("reason",result))}')
    return str((result.get('data') or {}).get('pgc_id',''))
