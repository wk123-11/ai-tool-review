#!/usr/bin/env python3
"""Fetch a URL through the proxy and print stripped text (first N chars)."""
import sys, re, html, urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
PROXY = "http://172.21.16.1:7890"


def main():
    url = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 3000
    use_proxy = "--direct" not in sys.argv
    op = urllib.request.build_opener(
        urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})) if use_proxy \
        else urllib.request.build_opener()
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8"})
    raw = op.open(req, timeout=30).read().decode("utf-8", "ignore")
    raw = re.sub(r"<script.*?</script>", " ", raw, flags=re.S)
    raw = re.sub(r"<style.*?</style>", " ", raw, flags=re.S)
    txt = re.sub(r"<[^>]+>", " ", raw)
    print(re.sub(r"\s+", " ", html.unescape(txt))[:n])


if __name__ == "__main__":
    main()
