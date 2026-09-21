#!/usr/bin/env python3
"""Set claude_input_chars for a given date in .token_log.json (last entry of that date)."""
import json, sys
from pathlib import Path

LOG = Path("/home/wk/ai-tool-review/.token_log.json")
date, chars = sys.argv[1], int(sys.argv[2])
log = json.loads(LOG.read_text())
for e in reversed(log["entries"]):
    if e.get("date") == date:
        e["claude_input_chars"] = chars
        break
LOG.write_text(json.dumps(log, indent=2, ensure_ascii=False))
print(f"{date}: claude_input_chars = {chars}")
