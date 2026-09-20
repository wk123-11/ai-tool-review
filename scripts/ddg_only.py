#!/usr/bin/env python3
"""DuckDuckGo-lite search (via proxy). Usage: ddg_only.py "query" """
import sys, re, html, urllib.parse, urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
PROXY = "http://172.21.16.1:7890"


def strip(s):
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def main():
    q = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    op = urllib.request.build_opener(
        urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))
    url = "https://lite.duckduckgo.com/lite/?q=" + urllib.parse.quote(q)
    raw = op.open(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=30).read().decode("utf-8", "ignore")
    items = re.findall(r"""<a[^>]*class=['"]result-link['"][^>]*href="([^"]+)"[^>]*>(.*?)</a>""", raw, re.S)
    snips = re.findall(r"""<td[^>]*class=['"]result-snippet['"][^>]*>(.*?)</td>""", raw, re.S)
    for i, (link, title) in enumerate(items[:n]):
        print(f"{i+1}. {strip(title)}\n   {link}\n   {strip(snips[i])[:300] if i < len(snips) else ''}")


if __name__ == "__main__":
    main()
