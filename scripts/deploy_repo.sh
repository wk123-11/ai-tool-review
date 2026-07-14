#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
remote="$(git remote get-url origin 2>/dev/null || true)"
if [[ -z "$remote" ]]; then echo "ERROR: configure git remote origin first." >&2; exit 1; fi
if [[ "$remote" =~ https://[^/]*:[^@]+@github.com ]]; then echo "ERROR: origin contains embedded credentials." >&2; exit 1; fi
git add -A
if ! git diff --cached --quiet; then git commit -m "Update $(date +%Y-%m-%d)"; fi
git push -u origin main
