#!/usr/bin/env python3
"""Minimal search helper: DuckDuckGo Lite (via Windows Clash proxy), with retry + Bing fallback."""
import sys, re, html, time, urllib.parse, urllib.request

PROXY = "http://172.21.16.1:7890"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "zh-CN,zh;q=0.9"})
    return OPENER.open(req, timeout=30).read().decode("utf-8", "ignore")


def parse_ddg(raw, n):
    items = []
    for m in re.finditer(r"""<a[^>]*class=['"]result-link['"][^>]*href="([^"]+)"[^>]*>(.*?)</a>""", raw, re.S):
        items.append([m.group(1), re.sub(r"<[^>]+>", "", m.group(2))])
    snips = re.findall(r"""<td[^>]*class=['"]result-snippet['"][^>]*>(.*?)</td>""", raw, re.S)
    snips = [html.unescape(re.sub(r"<[^>]+>", " ", s)).strip() for s in snips]
    out = []
    for i, it in enumerate(items[:n]):
        s = re.sub(r"\s+", " ", snips[i] if i < len(snips) else "")[:400]
        out.append(f"{i+1}. {html.unescape(it[1])}\n   {it[0]}\n   {s}")
    return "\n".join(out)


def parse_bing(raw, n):
    out = []
    for m in re.finditer(r'<li class="b_algo".*?</li>', raw, re.S):
        block = m.group(0)
        a = re.search(r'<h2[^>]*>.*?<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', block, re.S)
        p = re.search(r'<p[^>]*>(.*?)</p>', block, re.S)
        if not a:
            continue
        title = html.unescape(re.sub(r"<[^>]+>", "", a.group(2)))
        snip = html.unescape(re.sub(r"<[^>]+>", " ", p.group(1))) if p else ""
        out.append(f"{len(out)+1}. {title}\n   {a.group(1)}\n   {re.sub(chr(92)+'s+', ' ', snip)[:400]}")
        if len(out) >= n:
            break
    return "\n".join(out)


def search(query, n=8):
    q = urllib.parse.quote(query)
    last = ""
    for attempt in range(3):
        try:
            raw = fetch("https://lite.duckduckgo.com/lite/?q=" + q)
            res = parse_ddg(raw, n)
            if res:
                return res
            last = "ddg empty"
        except Exception as e:
            last = f"ddg error {e}"
        time.sleep(4)
    # Bing fallback
    try:
        raw = fetch("https://www.bing.com/search?q=" + q + "&setlang=zh-CN&ensearch=0")
        res = parse_bing(raw, n)
        if res:
            return res
        last += " | bing empty"
    except Exception as e:
        last += f" | bing error {e}"
    return "(no results: " + last + ")"


if __name__ == "__main__":
    for q in sys.argv[1:]:
        print(f"\n===== QUERY: {q} =====")
        print(search(q))
        time.sleep(3)
