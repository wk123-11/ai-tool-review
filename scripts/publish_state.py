#!/usr/bin/env python3
"""Local, atomic, per-platform publication state."""
from datetime import datetime, timezone
from pathlib import Path
import json, os, tempfile
PROJECT_ROOT = Path(__file__).resolve().parents[1]
STATE_FILE = Path(os.environ.get('AI_TOOL_REVIEW_STATE_FILE', PROJECT_ROOT/'.local'/'publish_state.json'))
class AlreadyPublishedError(RuntimeError): pass
def load_state() -> dict:
    if not STATE_FILE.exists(): return {'version':1,'items':{}}
    try: data=json.loads(STATE_FILE.read_text(encoding='utf-8'))
    except (json.JSONDecodeError,OSError): return {'version':1,'items':{}}
    if not isinstance(data,dict): return {'version':1,'items':{}}
    data.setdefault('version',1); data.setdefault('items',{}); return data

def get_record(platform: str, content_id: str) -> dict | None:
    return load_state().get('items', {}).get(content_id, {}).get(platform)

def _legacy_title_exists(platform: str, title: str) -> bool:
    legacy=PROJECT_ROOT/'scripts'/f'.{platform}_published_ids'
    if not legacy.exists(): return False
    for line in legacy.read_text(encoding='utf-8',errors='replace').splitlines():
        parts=line.split('|',2)
        if len(parts)==3 and parts[2].removesuffix(' (with images)').strip()==title.strip(): return True
    return False
def assert_publishable(platform: str, content_id: str, title: str, *, force: bool=False) -> None:
    if force: return
    rec=load_state().get('items',{}).get(content_id,{}).get(platform)
    if rec and rec.get('status') in {'published','draft'}:
        raise AlreadyPublishedError(f'{content_id} already recorded on {platform}: {rec.get("remote_id","unknown")}')
    if _legacy_title_exists(platform,title):
        raise AlreadyPublishedError(f'Legacy log already contains this title on {platform}')
def record(platform: str, content_id: str, title: str, status: str, *, remote_id: str='', url: str='') -> None:
    state=load_state(); item=state['items'].setdefault(content_id,{})
    item[platform]={'status':status,'title':title,'remote_id':str(remote_id or ''),'url':url,'updated_at':datetime.now(timezone.utc).isoformat()}
    STATE_FILE.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='publish-state-',suffix='.json',dir=STATE_FILE.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f: json.dump(state,f,ensure_ascii=False,indent=2); f.write('\n')
        os.replace(tmp,STATE_FILE)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)
