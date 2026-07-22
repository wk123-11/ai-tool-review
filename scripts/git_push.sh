#!/usr/bin/env bash
# Read token and push
TOKEN=$(cat "$(dirname "$0")/.ghtoken")
export https_proxy=http://172.21.16.1:7890
cd "$(dirname "$0")/.."
git add -A
if git diff --cached --quiet; then
    echo "Nothing to commit."
    exit 0
fi
git commit -m "Update $(date +%Y-%m-%d)"
# Use GIT_ASKPASS to provide credentials
echo "#!/bin/sh
echo \"\$TOKEN\"
" > /tmp/git-askpass.sh
chmod +x /tmp/git-askpass.sh
GIT_ASKPASS=/tmp/git-askpass.sh git push "https://wk123-11@github.com/wk123-11/ai-tool-review.git" main 2>&1
