#!/bin/bash
# AI工具派 - 部署到 GitHub Pages
# 用法: ./scripts/deploy_repo.sh
set -e

TOKEN=$(cat /home/wk/ai-tool-review/scripts/.ghtoken)

cd /home/wk/ai-tool-review

# 设置远程仓库（使用 .ghtoken 中的 token）
git remote remove origin 2>/dev/null || true
git remote add origin "https://wk123-11:${TOKEN}@github.com/wk123-11/ai-tool-review.git"

# 推送到 GitHub
echo "=== 推送到 GitHub ==="
git add -A
git commit --allow-empty -m "Update $(date +%Y-%m-%d)" 2>/dev/null || true
git push -u origin main 2>&1

echo "=== 完成 ==="
