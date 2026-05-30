#!/usr/bin/env python3
"""
一键部署脚本：初始化 Git 仓库并推送到 GitHub Pages
"""
import os
import sys
import subprocess
from pathlib import Path

SITE_DIR = Path("/home/wk/ai-tool-review")
GITHUB_USER = "wk"  # 用户可修改

def run(cmd, cwd=None):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd or SITE_DIR)
    if result.returncode != 0:
        print(f"❌ Error: {result.stderr[:300]}")
        return False
    if result.stdout.strip():
        print(result.stdout[:300])
    return True

def main():
    print("=" * 50)
    print("AI工具派 · GitHub Pages 初始化部署")
    print("=" * 50)
    
    # 检查 git
    if not os.path.exists(str(SITE_DIR / ".git")):
        print("\n📦 初始化 Git 仓库...")
        run("git init")
        run("git checkout -b main")
    
    # 设置远程仓库
    remote_url = f"https://github.com/{GITHUB_USER}/ai-tool-review.git"
    result = subprocess.run(["git", "remote", "get-url", "origin"], 
                          capture_output=True, text=True, cwd=str(SITE_DIR))
    if result.returncode != 0:
        print(f"\n🔗 添加远程仓库: {remote_url}")
        run(f"git remote add origin {remote_url}")
    else:
        print(f"\n🔗 远程仓库已存在: {result.stdout.strip()}")
    
    # 首次提交
    print("\n📝 首次提交...")
    run("git add -A")
    run('git commit -m "Initial commit: AI工具派站点"')
    
    # 推送
    print("\n🚀 推送到 GitHub...")
    if run("git push -u origin main"):
        print("\n✅  部署完成！")
        print(f"   网站地址: https://{GITHUB_USER}.github.io/ai-tool-review/")
        print(f"   GitHub 仓库: {remote_url}")
        print("\n📋 接下来需要：")
        print("   1. 在仓库 Settings → Pages 确认部署状态")
        print("   2. 安装 jekyll-seo-tag 和 jekyll-sitemap 插件")
    else:
        print("\n❌ 推送失败，请检查 GitHub Token 是否正确")

if __name__ == "__main__":
    main()
