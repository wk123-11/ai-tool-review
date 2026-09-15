#!/usr/bin/env python3
"""Probe whether the stored Toutiao session cookie is still authenticated."""
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from secrets_config import load_toutiao_cookie

COOKIE = load_toutiao_cookie()
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/148 Safari/537.36'
H = {
    'Cookie': COOKIE,
    'User-Agent': UA,
    'Origin': 'https://mp.toutiao.com',
    'Referer': 'https://mp.toutiao.com/profile_v4/graphic/publish',
    'Accept': 'application/json, text/plain, */*',
}

PROBES = [
    'https://mp.toutiao.com/mp/agw/creator_center/user_info?aid=1231',
    'https://mp.toutiao.com/mp/agw/article/list?aid=1231&status=all&offset=0&count=1',
    'https://mp.toutiao.com/mp/agw/media/get_media_list?aid=1231&offset=0&count=1',
]


def get(url):
    req = urllib.request.Request(url, headers=H, method='GET')
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return f'HTTP{r.status} ' + r.read().decode('utf-8', 'replace')[:260]
    except urllib.error.HTTPError as e:
        return f'HTTP{e.code} ' + e.read().decode('utf-8', 'replace')[:260]
    except Exception as e:  # noqa: BLE001
        return 'ERR ' + str(e)[:200]


for u in PROBES:
    print(f'=== {u}\n{get(u)}\n')
