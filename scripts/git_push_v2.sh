#!/bin/bash
set -e

# Read token
TOKEN=$(cat /home/wk/ai-tool-review/scripts/.ghtoken | tr -d '\n')
echo "Token loaded: ${#TOKEN} chars"

export https_proxy=http://172.21.16.1:7890

cd /home/wk/ai-tool-review
git push "https://wk123-11:${TOKEN}@github.com/wk123-11/ai-tool-review.git" main
