#!/usr/bin/env python3
"""Deduplicate .token_log.json: keep only the LAST entry per date (in original order)."""
import json
from pathlib import Path

LOG = Path("/home/wk/ai-tool-review/.token_log.json")
log = json.loads(LOG.read_text())

entries = log.get("entries", [])
last_idx = {}
for i, e in enumerate(entries):
    last_idx[e.get("date")] = i
kept = [e for i, e in enumerate(entries) if last_idx[e.get("date")] == i]
log["entries"] = kept
LOG.write_text(json.dumps(log, indent=2, ensure_ascii=False))
print(f"dedup: {len(entries)} -> {len(kept)} entries")
