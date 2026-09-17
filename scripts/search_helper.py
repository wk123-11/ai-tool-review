#!/usr/bin/env python3
"""Search helper: Bing (cn.bing.com direct) with DDG-lite fallback. Prints top results."""
import sys, re, html, time, urllib.parse, urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
PROXY = "http://172.21.16.1:7890"


def fetch(url, proxy=None):
    h = {"User-Agent": UA, "Accept-Language": "zh-CN,zh;q=0.9",
         "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}
    op = urllib.request.build_opener(urllib.request.ProxyHandler({"http": proxy, "https": proxy})) if proxy \
        else urllib.request.build_opener()
    return op.open(urllib.request.Request(url, headers=h), timeout=30).read().decode("utf-8", "ignore")


def strip(s):
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def bing(query, n=8):
    raw = fetch("https://cn.bing.com/search?q=" + urllib.parse.quote(query) + "&mkt=zh-CN&count=15")
    out = []
    for m in re.finditer(r'<li class="b_algo".*?(?=<li class="b_algo"|</ol>)', raw, re.S):
        b = m.group(0)
        a = re.search(r'<h2[^>]*>.*?<a[^>]*?href="([^"]+)"[^>]*>(.*?)</a>', b, re.S)
        if not a:
            continue
        title = strip(a.group(2))
        link = a.group(1)
        if link.startswith("/"):
            link = "https://cn.bing.com" + link
        # unwrap bing redirect
        u = re.search(r"[?&]u=a1([^&]+)", link)
        if u:
            import base64
            try:
                link = base64.urlsafe_b64decode(u.group(1) + "===").decode("utf-8", "ignore")
            except Exception:
                pass
        p = re.search(r'<p class="b_lineclamp[^"]*"[^>]*>(.*?)</p>', b, re.S) or \
            re.search(r'<p[^>]*>(.*?)</p>', b, re.S)
        out.append((title, link, strip(p.group(1)) if p else ""))
        if len(out) >= n:
            break
    return out


def ddg(query, n=8):
    raw = fetch("https://lite.duckduckgo.com/lite/?q=" + urllib.parse.quote(query), proxy=PROXY)
    items, snips = [], []
    for m in re.finditer(r"""<a[^>]*class=['"]result-link['"][^>]*href="([^"]+)"[^>]*>(.*?)</a>""", raw, re.S):
        items.append((strip(m.group(2)), m.group(1)))
    for s in re.findall(r"""<td[^>]*class=['"]result-snippet['"][^>]*>(.*?)</td>""", raw, re.S):
        snips.append(strip(s))
    return [(t, l, snips[i] if i < len(snips) else "") for i, (t, l) in enumerate(items[:n])]


def run(q, n=8):
    for name, fn in (("bing", bing), ("ddg", ddg)):
        try:
            res = fn(q, n)
            if res:
                print(f"\n===== {name}: {q} =====")
                for i, (t, l, s) in enumerate(res):
                    print(f"{i+1}. {t}\n   {l}\n   {s[:350]}")
                return
        except Exception as e:
            print(f"[{name} failed: {e}]", file=sys.stderr)


if __name__ == "__main__":
    args = sys.argv[1:]
    for q in args:
        run(q)
        if len(args) > 1:
            time.sleep(2)
