#!/usr/bin/env python3
"""Search HN comments via Algolia API and print cleaned snippets."""
import sys, json, re, html, urllib.request, urllib.parse, time

PROXY = "http://172.21.16.1:7890"
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))


def search(query, n=6):
    url = ("https://hn.algolia.com/api/v1/search?query=" + urllib.parse.quote(query)
           + "&tags=comment&hitsPerPage=" + str(n))
    raw = OPENER.open(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=40).read()
    data = json.loads(raw.decode("utf-8", "ignore"))
    out = []
    for h in data.get("hits", []):
        text = re.sub(r"<[^>]+>", " ", html.unescape(h.get("comment_text") or ""))
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) < 60:
            continue
        out.append(f"- [{h.get('story_title','')}] {text[:400]}")
    return out


if __name__ == "__main__":
    for q in sys.argv[1:]:
        print(f"########## {q}")
        try:
            for line in search(q):
                print(line)
        except Exception as e:
            print(f"ERR {e}")
        print()
        time.sleep(2)
