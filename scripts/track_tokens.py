#!/usr/bin/env python3
"""Token consumption logger for ai-tool-review daily publish.

Usage:
    python3 scripts/track_tokens.py dict <article.md>         # 记录文章字数(DeepSeek写入)
    python3 scripts/track_tokens.py claude-in <article.md>     # 记录Claude审阅输入
    python3 scripts/track_tokens.py claude-out <chars>         # 记录Claude审阅输出
    python3 scripts/track_tokens.py publish <status>           # 记录发布状态(yes/no)
    python3 scripts/track_tokens.py show                        # 显示统计
"""

import json, os, sys
from pathlib import Path

LOG_FILE = Path(__file__).resolve().parent.parent / ".token_log.json"

# Rough token ratios (for Chinese text)
# Chinese: ~1.5-2 chars per token on average
# English: ~4 chars per token on average
CHINESE_CHARS_PER_TOKEN = 1.75  # conservative for mixed CN/EN
TOOL_CALL_OVERHEAD = 3000  # per tool call overhead
CLAUDE_CHARS_PER_TOKEN = 3.5  # Claude tokenizer is different

def load_log():
    if LOG_FILE.exists():
        return json.loads(LOG_FILE.read_text())
    return {"entries": []}

def save_log(log):
    LOG_FILE.write_text(json.dumps(log, indent=2, ensure_ascii=False))

def get_article_chars(article_path):
    text = Path(article_path).read_text(encoding="utf-8")
    # Strip YAML frontmatter
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            text = parts[2]
    return len(text)

def estimate_deepseek_tokens(chars):
    """Estimate tokens from Chinese text. Includes tool call overhead."""
    text_tokens = int(chars / CHINESE_CHARS_PER_TOKEN)
    # Writing article requires: web search (~5 calls * 500 tokens response),
    # writing (~article_tokens), tool calls (~15 calls * 200 tokens input)
    input_tokens = text_tokens * 2 + 15000  # prompt + few-shot + system
    output_tokens = text_tokens + 3000  # article body + reasoning
    return {"input": input_tokens, "output": output_tokens, "total": input_tokens + output_tokens}

def edit_log(cmd, args):
    log = load_log()
    today = args[0] if args else "unknown"

    if cmd == "dict":
        # Record article character count and estimate DeepSeek tokens
        # args: [date, article_path] - article_path may not exist yet
        article_path = args[1] if len(args) > 1 else None
        if not article_path or not Path(article_path).exists():
            # Try to find today's article in _posts/
            articles = sorted(Path(LOG_FILE.parent / "_posts").glob(f"{today}-*.md"))
            article_path = str(articles[0]) if articles else None
        
        chars = get_article_chars(article_path) if article_path and Path(article_path).exists() else 0
        tokens = estimate_deepseek_tokens(chars) if chars else {"input": 0, "output": 0, "total": 0}
        
        entry = {
            "date": today,
            "article_chars": chars,
            "deepseek_tokens": tokens,
            "claude_input_chars": 0,
            "claude_output_chars": 0,
            "publish_success": False
        }
        log["entries"].append(entry)
        print(f"Recorded: {today} | article={chars} chars | DeepSeek ~{tokens['total']} tokens")

    elif cmd == "claude-in":
        # Claude review input = article content
        article_path = args[1] if len(args) > 1 else None
        chars = get_article_chars(article_path) if article_path else 0
        
        # Claude Code CLI messages include system prompt (~1000 chars),
        # the article content, and the user's review prompt (~300 chars)
        claude_input = chars + 1300
        if log["entries"] and log["entries"][-1]["date"] == today:
            log["entries"][-1]["claude_input_chars"] = claude_input
        print(f"Recorded Claude input: ~{claude_input} chars (={int(claude_input/CLAUDE_CHARS_PER_TOKEN)} tokens)")

    elif cmd == "claude-out":
        # Claude review output
        if len(args) < 2:
            print("Need output char count")
            return
        chars = int(args[1])
        if log["entries"] and log["entries"][-1]["date"] == today:
            log["entries"][-1]["claude_output_chars"] = chars
        print(f"Recorded Claude output: ~{chars} chars (={int(chars/CLAUDE_CHARS_PER_TOKEN)} tokens)")

    elif cmd == "publish":
        status = args[1] if len(args) > 1 else "no"
        if log["entries"] and log["entries"][-1]["date"] == today:
            log["entries"][-1]["publish_success"] = (status == "yes")
        print(f"Publish status: {status}")

    elif cmd == "show":
        if not log["entries"]:
            print("No token data yet.")
            return
        total_tokens = 0
        total_cost = 0.0
        print(f"{'Date':<12} {'Article':<20} {'DeepSeek':<15} {'Claude In':<12} {'Claude Out':<13} {'Published':<10}")
        print("-" * 90)
        for e in log["entries"]:
            ds = e.get("deepseek_tokens", {}).get("total", 0)
            cl_in = int(e.get("claude_input_chars", 0) / CLAUDE_CHARS_PER_TOKEN)
            cl_out = int(e.get("claude_output_chars", 0) / CLAUDE_CHARS_PER_TOKEN)
            total = ds + cl_in + cl_out
            total_tokens += total
            # DeepSeek v4 Flash: ~$0.15/M input, ~$0.60/M output
            ds_input = e.get("deepseek_tokens", {}).get("input", 0)
            ds_output = e.get("deepseek_tokens", {}).get("output", 0)
            ds_cost = (ds_input / 1_000_000 * 0.15) + (ds_output / 1_000_000 * 0.60)
            # Claude (Pro subscription, no additional cost per API call in CLI mode)
            total_cost += ds_cost
            pub = "✅" if e.get("publish_success") else "❌"
            title = f"{e.get('article_chars',0)} chars"
            print(f"{e['date']:<12} {title:<20} {ds:<15} {cl_in:<12} {cl_out:<13} {pub:<10}")
        print("-" * 90)
        print(f"Total: {total_tokens} tokens | Est. cost: ¥{total_cost * 7.3:.2f} (DeepSeek only, at ¥7.3/$)")

    save_log(log)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    args = sys.argv[2:]
    edit_log(cmd, args)
