#!/usr/bin/env python3
"""Create a Toutiao-ready copy of the article with image lines removed (same stem => same content_id)."""
import re, sys
from pathlib import Path
src = Path(sys.argv[1]); dst_dir = Path(sys.argv[2]); dst_dir.mkdir(parents=True, exist_ok=True)
text = src.read_text(encoding='utf-8')
out = '\n'.join(l for l in text.splitlines() if not re.match(r'^\s*!\[[^\]]*\]\([^)]*\)\s*$', l))
dst = dst_dir / src.name
dst.write_text(out, encoding='utf-8')
print(f'wrote {dst} ({len(out)} chars, images stripped)')
