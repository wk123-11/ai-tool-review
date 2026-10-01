#!/usr/bin/env python3
import sys
sys.path.insert(0, 'scripts')
from secrets_config import load_toutiao_cookie, load_zhihu_cookie
tc = load_toutiao_cookie(); zc = load_zhihu_cookie()
print('toutiao cookie len', len(tc), 'has sessionid:', 'sessionid' in tc)
print('zhihu cookie len', len(zc), 'has z_c0:', 'z_c0' in zc)
