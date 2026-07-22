#!/bin/bash
set -e
cd /home/wk/ai-tool-review
TOKEN_RAW=*** /home/wk/ai-tool-review/scripts/.ghtoken)
TOKEN=$(echo "$TOKEN_RAW" | tr -d '\n')
export https_proxy=http://172.21.16.1:7890
git remote set-url origin "https://wk123-11:${TOKEN}@github.com/wk123-11/ai-tool-review.git"
git push origin main
