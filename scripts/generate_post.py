#!/usr/bin/env python3
"""
AI工具派 · 自动内容生成器
每天由 cron 调用，生成一篇 SEO 优化文章并提交到 GitHub
"""
import os
import sys
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

SITE_DIR = Path("/home/wk/ai-tool-review")
POSTS_DIR = SITE_DIR / "_posts"
SCRIPTS_DIR = SITE_DIR / "scripts"

# 文章选题池 — 覆盖面广、搜索量大的长尾关键词
TOPICS = [
    # AI工具评测
    ("2025年最值得使用的AI写作工具评测对比", "ai-writing-tools-review", "AI写作"),
    ("5款免费AI图片生成工具实测，哪款最适合你？", "free-ai-image-generators", "AI绘图"),
    ("AI编程助手对比：Cursor vs Copilot vs Codeium", "ai-coding-assistant-comparison", "AI编程"),
    ("2025年AI视频生成工具横评：可灵、Sora、Veo对比", "ai-video-generators-2025", "AI视频"),
    ("用AI做PPT的工具推荐，10分钟搞定演示文稿", "ai-ppt-maker-tools", "效率工具"),
    ("AI语音转文字工具评测：讯飞、Whisper、通义听悟", "ai-speech-to-text-tools", "AI语音"),
    ("6款AI翻译工具实测，哪个翻译最准确？", "best-ai-translators", "AI翻译"),
    ("AI搜索引擎对比：Perplexity、天工、360AI搜索哪个好用", "ai-search-engine-comparison", "AI搜索"),
    ("AI做表格和数据分析的工具推荐", "ai-data-analysis-tools", "效率工具"),
    ("AI设计工具推荐：Canva AI、Midjourney、Stable Diffusion", "ai-design-tools", "AI设计"),

    # 效率提升
    ("工作效率翻倍的10个AI自动化工作流", "ai-automation-workflows", "效率方法"),
    ("用AI管理日程和任务：最佳AI助手推荐", "ai-task-manager-tools", "效率工具"),
    ("AI笔记工具推荐：Notion AI、Obsidian、Mem对比", "ai-note-taking-tools", "效率工具"),
    ("5个提升阅读效率的AI工具", "ai-reading-tools", "效率方法"),
    ("邮件处理太慢？用AI自动回复和分类", "ai-email-automation", "效率方法"),
    ("AI会议纪要工具推荐，开会不再手写笔记", "ai-meeting-notes-tools", "效率工具"),
    ("用AI做读书笔记，效率提升10倍", "ai-book-notes", "效率方法"),

    # 副业赚钱
    ("用AI做短视频副业：完整教程", "ai-short-video-side-hustle", "副业赚钱"),
    ("AI绘画接单指南：如何用Midjourney赚钱", "ai-art-freelance-guide", "副业赚钱"),
    ("零成本AI副业：用ChatGPT写小红书笔记", "ai-xiaohongshu-content", "副业赚钱"),
    ("AI配音和有声书制作，在家就能做的副业", "ai-audiobook-side-hustle", "副业赚钱"),
    ("用AI做跨境电商文案，每月多赚3000", "ai-cross-border-ecommerce", "副业赚钱"),
    ("AI编程接单：不会代码也能做外包项目", "ai-coding-freelance", "副业赚钱"),

    # 工具推荐合集
    ("2025年必备的20个免费AI工具", "top-free-ai-tools-2025", "工具合集"),
    ("学生党必看的10个免费AI学习工具", "ai-tools-for-students", "工具合集"),
    ("自媒体人必备AI工具清单", "ai-tools-for-content-creators", "工具合集"),
    ("程序员效率提升AI工具推荐", "ai-tools-for-programmers", "工具合集"),
]

def get_today_topic():
    """根据日期从选题池中选择一个"""
    today = datetime.now(timezone.utc)
    day_of_year = today.timetuple().tm_yday
    idx = day_of_year % len(TOPICS)
    return TOPICS[idx]

def render_post(title, content, categories, date_str):
    """渲染 Jekyll 文章文件"""
    slug = title.lower()\
        .replace(' ', '-')\
        .replace('：', '')\
        .replace('？', '')\
        .replace('，', '')\
        .replace('、', '-')\
        .replace('——', '')\
        .replace('!', '')\
        .replace('?', '')\
        .replace(':', '')\
        .replace(',', '')\
        .replace('.', '')
    # truncate to reasonable length
    slug = slug[:80]
    
    lines = [
        "---",
        f"layout: post",
        f"title: {title}",
        f"date: {date_str}",
        f"categories: [{categories}]",
        f"description: {content[:150].strip()}",
        "---",
        "",
        content.strip(),
        "",
    ]
    return "\n".join(lines), f"{date_str}-{slug}.md"

def build_site():
    """构建 Jekyll 站点用于调试"""
    try:
        result = subprocess.run(
            ["jekyll", "build", "--source", str(SITE_DIR), "--destination", str(SITE_DIR / "_site")],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            print(f"✅ Site built successfully")
            return True
        else:
            print(f"❌ Build error: {result.stderr[:500]}")
            return False
    except FileNotFoundError:
        print("⚠️  jekyll not installed locally, skipping build check")
        return True  # GitHub Pages will build it

def git_commit_and_push():
    """提交并推送文章到 GitHub"""
    os.chdir(str(SITE_DIR))
    # git add
    subprocess.run(["git", "add", "-A"], capture_output=True)
    # commit
    result = subprocess.run(
        ["git", "commit", "-m", f"auto: new post {datetime.now().strftime('%Y-%m-%d %H:%M')}"],
        capture_output=True, text=True
    )
    if "nothing to commit" in result.stdout or "nothing to commit" in result.stderr:
        print("ℹ️  Nothing to commit")
        return
    print(result.stdout[:200])
    # push
    push_result = subprocess.run(["git", "push"], capture_output=True, text=True)
    if push_result.returncode == 0:
        print(f"✅ Pushed to GitHub successfully")
    else:
        print(f"❌ Push failed: {push_result.stderr[:300]}")

if __name__ == "__main__":
    print("=" * 40)
    print("AI工具派 · 内容生成器")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 40)
    
    topic = get_today_topic()
    print(f"\n📋 今日选题: {topic[0]}")
    
    # 这里由 cron job 中的 AI agent 填充内容
    # 脚本作为占位符和部署工具
    # 实际内容生成由 hermes cron job 的 AI 完成
    
    print("\n📝 等待 AI 生成内容...")
    print(f"   topic: {topic[0]}")
    print(f"   slug: {topic[1]}")
    print(f"   category: {topic[2]}")
    print("\n✅ 准备就绪")
    print(f"   文章路径: {POSTS_DIR}/")
    print(f"   站点目录: {SITE_DIR}")
