#!/usr/bin/env python3
"""Probe whether the stored Zhihu session cookie is still authenticated."""
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from secrets_config import load_zhihu_cookie

COOKIE = load_zhihu_cookie()
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/148 Safari/537.36'
H = {
    'Cookie': COOKIE,
    'User-Agent': UA,
    'Referer': 'https://zhuanlan.zhihu.com/write',
    'Accept': 'application/json, text/plain, */*',
}

PROBES = [
    'https://www.zhihu.com/api/v4/me',
    'https://www.zhihu.com/api/v4/me/column?limit=5',
]


def get(url):
    req = urllib.request.Request(url, headers=H, method='GET')
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return f'HTTP{r.status} ' + r.read().decode('utf-8', 'replace')[:300]
    except urllib.error.HTTPError as e:
        return f'HTTP{e.code} ' + e.read().decode('utf-8', 'replace')[:300]
    except Exception as e:  # noqa: BLE001
        return 'ERR ' + str(e)[:200]


for u in PROBES:
    print(f'=== {u}\n{get(u)}\n')
