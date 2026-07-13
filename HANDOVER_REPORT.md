# AI工具派 — 每日内容生成与多平台分发 完整交接报告

> 编写日期：2026-07-12
> 目标读者：ChatGPT / Codex（即将接手的 AI agent）
> 目的：完整了解该系统如何运作、如何维护、如何排查故障

---

## 1. 项目概览

**项目名称**：AI工具派（ai-tool-review）
**项目路径**：`/home/wk/ai-tool-review/`
**GitHub 仓库**：`wk123-11/ai-tool-review`
**目标**：每天全自动生成一篇 AI 工具横评文章，发布到三个平台：
- **GitHub Pages**（https://wk123-11.github.io/ai-tool-review/）— 博客站点，Jekyll 静态网站
- **头条号**（mp.toutiao.com）— 中国内容平台
- **知乎专栏**（zhuanlan.zhihu.com）— 中国知识平台

**运行环境**：WSL (Windows Subsystem for Linux)，通过 Hermes（AI agent 调度器）的 cron 在每天 08:00 自动触发。

**当前状态**：已稳定运行约 6 周（2026-05-28 ~ 至今），累计生成 ~37 篇文章。头条号/知乎阅读量极低（个位数），收入为 0。内容收益不是重点——用户已明确转向其他变现方向（闲鱼/接单），但每日发布继续运行不中断。

---

## 2. 系统架构总览

```
┌──────────────────────────────────────────────────────┐
│  Hermes Cron (cron ID: 43651f042949)                │
│  每日 08:00 触发，递送微信通知                        │
│  模型: deepseek-v4-flash (provider: deepseek)         │
│  启用工具集: terminal, file, web                      │
└─────────────────────┬────────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────────────┐
│  AI Agent (DeepSeek v4 Flash)                       │
│  加载 skill: ai-tool-review-pipeline                │
│  按 7 步执行全流程                                   │
└─────────────────────┬────────────────────────────────┘
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
    [选题+研究]  [写作]  [配图]
          │           │           │
          └───────────┼───────────┘
                      ▼
            markdown 文章存入
         _posts/YYYY-MM-DD-slug.md
                      │
                      ▼
    ┌─────────────────────────────────┐
    │ 质量审阅 (Claude Code CLI)      │
    │ 定价准确性 + 伪第一人称 + 事实   │
    │ 最多 2 轮修复循环              │
    │ 兜底: Claude 失败则 DeepSeek    │
    │      自行审阅                   │
    └─────────────┬───────────────────┘
                  │
                  ▼
    ┌────────────────────────────────────────────┐
    │  发布到三个平台                             │
    │                                            │
    │  1. GitHub Pages (git push)                │
    │     └─ 图片: raw.githubusercontent.com     │
    │                                            │
    │  2. 头条号 (publish_toutiao.py)             │
    │     └─ 图片: 先上传头条 CDN                │
    │        (/spice/image 接口)                  │
    │        → image-tt-private.toutiao.com      │
    │                                            │
    │  3. 知乎专栏 (publish_zhihu.py)             │
    │     └─ 图片: raw.githubusercontent.com     │
    │        需要 x-zse-96 签名                  │
    └────────────────────────────────────────────┘
```

---

## 3. 项目目录结构

```
/home/wk/ai-tool-review/
├── _posts/                         # 文章源文件 (Jekyll markdown)
│   └── 2026-07-12-ai-writing-tools-comparison.md  # 命名: YYYY-MM-DD-slug.md
├── images/                         # 配图 (Unsplash 下载)
│   ├── ai-writing-desk-laptop.jpg
│   ├── ai-writing-desk-creative.jpg
│   └── ...
├── scripts/
│   ├── publish_toutiao.py          # 头条号发布 (markdown→HTML + API)
│   ├── publish_zhihu.py            # 知乎发布 (markdown→HTML + API + 签名)
│   ├── upload_images.py            # 上传图片 + 替换URL + 发布头条号 (含图版)
│   ├── zhihu_zse96.py             # 知乎 x-zse-96 签名算法 (Python 逆移植)
│   ├── track_tokens.py            # Token 消耗统计
│   ├── make_preview.py            # 生成 base64 图片嵌入的预览 HTML
│   ├── deploy_repo.sh             # Git 部署到 GitHub
│   ├── git-askpass.sh             # Git 自动认证
│   ├── .ghtoken                   # GitHub personal access token
│   ├── .toutiao_cookie            # 头条号 cookie (明文)
│   ├── .zhihu_cookie              # 知乎 cookie (明文)
│   ├── .toutiao_published_ids     # 头条号发布记录日志
│   ├── .zhihu_published_ids       # 知乎发布记录日志
│   ├── generate_post.py           # 早期文章生成脚本
│   ├── deploy.py                  # 备选部署脚本
│   ├── check_token.py             # Token 有效性检查
│   ├── test_ghtoken.py            # GitHub Token 测试
│   ├── test_toutiao_upload.py     # 头条号上传测试
│   ├── debug_upload.py / debug_upload2.py  # 图片上传调试
│   ├── fix_zhihu_images.py        # 知乎图片修复 (成功率低，参考用)
│   └── try_baseline.py            # 基线测试
├── .git/                          # Git 仓库
├── .github/                       # GitHub Actions (如需)
├── .token_log.json                # Token 消耗日志
├── _config.yml                    # Jekyll 配置
├── index.md                       # 博客首页
└── about.md                       # 关于页
```

---

## 4. 每日执行流程（7 步）

### Step 1: 选题与写作

Agent 用 DeepSeek v4 Flash 模型进行：
- 选题：自动决定今天的主题（AI写作/AI编程/AI视频/AI翻译/AI PPT/AI搜索/AI绘图等），主题轮换不重复
- 研究：用 `web_search` 搜索每个工具的最新版本/定价/用户评价（Reddit、知乎、V2EX）
- 写作：输出 Jekyll markdown 格式文章，保存到 `_posts/YYYY-MM-DD-slug.md`

**文章格式规范**：
```markdown
---
layout: post
title: "标题（2-30字，含关键搜索词）"
date: 2026-07-12 08:00:00 +0800
categories: [AI工具, 写作]
tags: [AI写作, ChatGPT, Claude, 2026]
---

# 标题

![描述](/images/file.jpg)

## 概述
(市场背景 + 文章主题说明)

## 工具A — 一句话描述
**价格**：xxx
(详细介绍 + 用户评价引用 + 适合人群)

## 工具B ...
...

## 横向对比
| 工具 | 定价 | 特色 | 适合 |
|------|------|------|------|
| ... | ... | ... | ... |

## 推荐
(按场景推荐)

## 趋势展望
(行业趋势)
```

**内容质量铁律**：
- 每个产品的定价必须从官网验证（两个独立来源交叉比对）
- 禁止伪第一人称（"我试了"、"我花了一周"）
- 必须引用真实用户评价，注明来源
- 配图 4-6 张，每张必须与主题强相关（禁止抽象通用图）
- 相邻文章禁止复用图片

### Step 2: 记录 DeepSeek Token 消耗

```bash
python3 scripts/track_tokens.py dict "$(date +%Y-%m-%d)" _posts/<文章>.md
```

估算逻辑（`track_tokens.py`）：
- 中文约 1.75 chars/token
- 包含工具调用开销（搜索 ~15,000 input tokens、写作输出）
- 单篇成本约 ¥0.04-0.08（DeepSeek v4 Flash）

### Step 3: Git Push (GitHub Pages)

```bash
export https_proxy=http://172.21.16.1:7890  # 仅 git 需要代理
cd /home/wk/ai-tool-review
git add -A && git commit -m "Update $(date +%Y-%m-%d)"
# 使用 deploy_repo.sh 或手动 git push
bash scripts/deploy_repo.sh
```

认证方式：`.ghtoken` 文件中的 GitHub personal access token，通过 `git-askpass.sh` 或直接写入 remote URL。

### Step 4: Claude Code 交叉审阅

```bash
export https_proxy=http://172.21.16.1:7890
/home/wk/.hermes/node/bin/claude -p "阅读文章 <路径>，只检查三件事：1.定价与官网一致？2.伪第一人称？3.事实错误？输出格式：[审核结果] 通过/不通过 [问题列表] 输出字数不要超过300字" --dangerously-skip-permissions --max-turns 5
```

审阅后：
- 通过 → 继续发布
- 不通过 → 修复后重审（最多 2 轮）
- Claude 命令失败 → 兜底：DeepSeek 自行审阅

Claude Code 路径：`/home/wk/.hermes/node/bin/claude`（v2.1.161，通过 `npm install -g @anthropic-ai/claude-code` 安装）

### Step 5: 头条号发布

**图片上传**（如果今天图片没缓存过）：
```bash
# 上传图片到头条 CDN (/spice/image 接口)
python3 scripts/upload_images.py _posts/<文章>.md
```

上传接口详情：
- **端点**：`POST https://mp.toutiao.com/spice/image?upload_source=20020002&aid=1231&device_platform=web`
- **字段名**：`image`（multipart file）
- **必选 Header**：`x-secsdk-csrf-token`（从 cookie 中提取 `passport_csrf_token`）
- **必选 Header**：`Referer: https://mp.toutiao.com/profile_v4/graphic/publish`
- **必选**：完整 session cookie
- **返回**：`image_url`（`image-tt-private.toutiao.com` 域名，仅头条号内部能访问）

**发布文章**：
```bash
python3 scripts/publish_toutiao.py _posts/<文章>.md
```

头条号 API：
- **端点**：`POST https://mp.toutiao.com/mp/agw/article/publish?source=mp&type=article&aid=1231`
- **参数**：`title`、`content`（HTML）、`save=1`（直接发布）、`extra`（含字数等元数据）
- **成功返回**：`pgc_id`（文章 ID）

图片策略：头条号不接受外部 URL（会返回 code 7115），必须先用 `/spice/image` 上传到头条 CDN，再用 CDN URL 替换 markdown 中的图片路径。

Cookie 过期时会返回 `code: 1005`，需要重新获取。

### Step 6: 知乎发布

```bash
python3 scripts/publish_zhihu.py _posts/<文章>.md
```

知乎发布三阶段：
1. `POST /api/articles/drafts` → 创建草稿，获得 `article_id`
2. `PATCH /api/articles/{id}/draft` → 更新草稿内容
3. `PUT /api/articles/{id}/publish` → 发布

认证方式：
- **Cookie**：需要 `d_c0`、`z_c0`、`_xsrf`
- **x-zse-96 签名**：知乎反爬虫机制，由 `zhihu_zse96.py` 生成
  - 算法：MD5(`101_3_3.0+{api_path}+{d_c0}`) → 自定义 32 轮分组加密 → 自定义 base64
  - 此算法逆向自网页端 JS，已验证可用

图片策略：知乎接受 `raw.githubusercontent.com` 的图片 URL（与 GitHub Pages 共用），无需单独上传。发布脚本会自动将相对路径 `/images/xxx.jpg` 替换为完整 GitHub raw URL。

**知乎 24h 发布冷却**：同一账号 24h 内只能正式发布一篇文章。发布频率过高会返回 `code: 4031 PublishArticleLimitException`。

**已发布文章不可通过 API 修图**：`PUT /publish` 对已发布文章返回 400，只能 PATCH 草稿内容但无法重新发布。图片一旦裂了只能等 24h 后新建文章重发。

### Step 7: 提交 Token 日志

```bash
git add .token_log.json && git commit -m "token stats $(date +%Y-%m-%d)" && git push
```

---

## 5. 关键认证凭证管理

所有凭证以明文文件存储在 `scripts/` 目录下：

| 文件 | 内容 | 用途 |
|------|------|------|
| `.ghtoken` | GitHub Personal Access Token | git push 认证 |
| `.toutiao_cookie` | 头条号完整 cookie 字符串 | 头条号 API 认证 + 图片上传 |
| `.zhihu_cookie` | 知乎完整 cookie 字符串 | 知乎 API 认证（需含 d_c0, z_c0, _xsrf）|

**Cookie 会过期**，症状：
- 头条号：返回 `code: 1005` 或跳转登录页
- 知乎：返回 HTTP 302 跳转登录页，或 API 返回错误

**更新方法**：
1. 在 Windows 浏览器中登录头条号/知乎
2. F12 → Application → Cookies → 复制完整 cookie 字符串
3. 写入对应文件：`echo "cookie_string" > scripts/.toutiao_cookie`

**GitHub Token 过期**：
- 在 https://github.com/settings/tokens 生成新 classic token（勾选 repo 权限）
- 写入 `scripts/.ghtoken`

---

## 6. Markdown → HTML 转换规则

两个发布脚本各自独立实现了 markdown → HTML 转换（不从同一库导入，需同步维护）：

支持的语法：
- `**粗体**` → `<strong>`
- `*斜体*` → `<em>`
- `` `代码` `` → `<code>`
- `[链接](url)` → `<a href="url" rel="nofollow">`
- `![图片](url)` → `<img src="url" style="max-width:100%">`
- `#~#### 标题` → `<h1>~<h4>`
- `> 引用` → `<blockquote>`
- `- 无序列表` → `<ul><li>`
- `1. 有序列表` → `<ol><li>`
- `|表格|` → `<table><thead><tbody>`
- `---` → `<hr>`

知乎的 `_inline_format()` 链接加 `rel="nofollow"`（头条号也加了 `rel="nofollow"`），头条号的链接额外加 `target="_blank"`。

---

## 7. Hermes Cron 配置详情

```
Job ID:      43651f042949
Name:        ai-tool-review-daily
Schedule:    0 8 * * * (每天 08:00 CST)
Model:       deepseek-v4-flash (provider: deepseek)
Delivery:    local (结果不推微信；之前失败过因 iLink 限流)
Skill:       ai-tool-review-pipeline
Toolsets:    terminal, file, web
Enabled:     true
```

### ⚠️ Cron 常见陷阱

1. **不显式 pin 模型会导致静默失败**
   - 如果全局默认模型变更或损坏，cron 会静默跟随并产生垃圾输出
   - `last_status: ok` 不等于真正成功（调度器不校验输出质量）
   - 创建/更新 cron 时必须设置 `model` 和 `provider`

2. **delivery 默认是 `local`**
   - 必须显式设为 `weixin:o9cq80whDQHB9v8MlJlzxO_0fl7Q@im.wechat`
   - `deliver=local` 时文章正常发布但用户收不到推送

3. **更新 cron prompt 时 delivery/model 会被重置**
   - 每次 `cronjob action=update` 时必须重新指定 `deliver`、`model`

4. **Skill 和 Prompt 双重加载冲突**
   - cron 同时加载 skill（ai-tool-review-pipeline）和 prompt
   - 如果两者指令不一致，Agent 可能跟随 skill 的旧版本

5. **DeepSeek "(Wait!)" 自说自话循环**
   - 模型在复杂多步任务中可能进入英文自言自语模式
   - 零工具调用，产生垃圾输出但 status=ok
   - 预防：prompt 中禁止英文、禁止自言自语、给具体 shell 命令

---

## 8. 质量保障机制

### 数据准确性
- 定价必须从 2 个独立来源交叉验证
- 产品名称/版本/分类必须从官网确认
- 计量单位和数量级必须核实
- 对比表不能遗漏正文涉及的能力维度

### Claude Code 交叉审阅
- 独立的 Claude Pro 订阅（¥0 额外费用）
- 审阅范围：定价、伪第一人称、事实错误
- 修复循环：最多 2 轮，不通过则跳过发布
- 兜底：Claude 命令失败时 DeepSeek 自行审阅
- 需要代理访问（`https_proxy=http://172.21.16.1:7890`）

### Token 成本
- DeepSeek v4 Flash：约 ¥0.04-0.08/篇
- Claude Code 审阅：Pro 订阅已付，不计额外 API 费用
- 每月约 ¥1.2-2.4 运营成本

---

## 9. 网络与代理

**代理设置**（WSL 环境）：仅以下操作需要代理：
- `git` 操作（push/pull/clone 到 GitHub）
- `claude` CLI 调用

**代理配置**：
```bash
export https_proxy=http://172.21.16.1:7890
# 172.21.16.1 是 Windows 宿主机 IP（WSL 内部网桥）
# 7890 是 Clash/v2ray 代理端口
```

**不需要代理的操作**：
- DeepSeek API（直连国内）
- 头条号 API（国内服务）
- 知乎 API（国内服务）
- Unsplash 下载（直连）

---

## 10. 预览机制

```bash
cd /home/wk/ai-tool-review
python3 scripts/make_preview.py
```

`make_preview.py` 特点：
- 纯 Python stdlib，无外部依赖
- 手写 markdown 解析（不依赖 markdown 库）
- 图片转换为 base64 data URL 嵌入 HTML（单文件，离线可看）
- 生成 `preview-<日期>.html`
- 复制到 Windows 桌面后双击即可在浏览器查看：
  ```bash
  cp preview-*.html /mnt/c/Users/admin/Desktop/
  ```

---

## 11. 已知限制与历史事故

### 已修复的事故
| 日期 | 事故 | 原因 | 修复 |
|------|------|------|------|
| 2026-06-01 | AI 虚构定价（Copilot Business $39 实为 $19） | 未做双重验证 | 增加数据准确性铁律 |
| 2026-06-01 | cron agent 跑偏，搜索无关内容 | prompt 太软 | prompt 加入禁止行为区 |
| 2026-06-03 | cron 静默失败（模型未 pin） | 默认 ollama 模型崩溃 | pin 模型到 deepseek |
| 2026-06-03 | Claude 审阅 command not found | cron 环境中无 claude 命令 | 使用绝对路径 |
| 2026-06-03 | 图片上传端点错误（1053 错误） | 用了废弃的 `/mp/agw/...` | 切换到 `/spice/image` |
| 2026-06-03 | DeepSeek "(Wait!)" 循环 | 复杂任务超过工作记忆 | prompt 约束禁止自言自语 |

### 持续存在的限制
1. **头条号 Cookie 有效期有限**：需定期手动更新
2. **知乎 24h 发布冷却**：一天只能正式发布一篇
3. **WeChat 推送可能失败**：iLink 限流，不影响文章发布但用户收不到通知
4. **知乎已发布文章不可通过 API 修图**：图片裂了只能手动网页端修复
5. **头条号不接受外部图片 URL**：必须上传到自家 CDN
6. **收入几乎为零**：用户已知并接受，内容平台非变现主力

---

## 12. 日常维护检查清单

### 每日检查
```bash
# 1. 查看今天有没有新文章
ls -lt /home/wk/ai-tool-review/_posts/

# 2. 检查 cron 状态
cronjob action='list'  # 查看 last_run_at 和 last_status

# 3. 检查头条号
# 浏览器打开 https://mp.toutiao.com → 已发布文章

# 4. 检查知乎
# 浏览器打开 https://zhuanlan.zhihu.com → 你的专栏
```

### 故障排查
```bash
# 文章没生成？
# → 检查 cron last_status、查看会话记录
session_search(query="ai-tool-review-daily")

# 头条号发布失败？
# → 检查 cookie 是否过期
python3 -c "
import urllib.request
req = urllib.request.Request('https://mp.toutiao.com/profile_v4/graphic/publish')
# 带 cookie 请求，看是否跳到登录页
"

# 知乎发布失败？
# → 检查 cookie 中 d_c0、z_c0 是否有效
# → 检查 x-zse-96 签名是否正确（zhihu_zse96.py 算法未变）

# GitHub push 失败？
# → 检查 .ghtoken 是否过期
# → 检查代理是否通：curl -x http://172.21.16.1:7890 https://api.github.com
```

### Cookie 更新
```
头条号 cookie 获取步骤：
1. Windows 浏览器打开 mp.toutiao.com 并登录
2. F12 → Application → Cookies → mp.toutiao.com
3. 复制所有 cookie 拼接成字符串
4. echo "cookie_string" > /home/wk/ai-tool-review/scripts/.toutiao_cookie

知乎 cookie 获取步骤：
1. Windows 浏览器打开 zhuanlan.zhihu.com 并登录
2. F12 → Application → Cookies → .zhihu.com
3. 复制所有 cookie（确保含 d_c0、z_c0、_xsrf）
4. echo "cookie_string" > /home/wk/ai-tool-review/scripts/.zhihu_cookie
```

---

## 13. Skill 文件位置

主要的 skill 文档：
- Skill: `~/.hermes/skills/content-publishing/ai-tool-review-pipeline/SKILL.md`
- 参考文档（在 skill 目录的 `references/` 子目录下）：
  - `toutiao-automation.md` — 头条号 API 完整指南
  - `zhihu-automation.md` — 知乎 API 完整指南
  - `toutiao-image-upload.md` — 头条号图片上传细节
  - `zhihu-operational-rules.md` — 知乎运营规则（频率限制等）
  - `data-accuracy-checklist.md` — 数据准确性检查清单
  - 以及多篇事故分析记录（cron 跑偏、模型失败、"(Wait!)" 循环等）

---

## 14. AI 接手注意事项

### 给 ChatGPT / Codex 的操作要点

1. **这是 WSL 环境**，文件路径是 Linux 风格（`/home/wk/`），Windows 文件在 `/mnt/c/`、`/mnt/d/` 等

2. **发布脚本使用 Python 3 stdlib 纯标准库**，没有 pip 依赖——无需 `pip install`

3. **输出文章时严格遵守 Jekyll frontmatter 格式**：`title` 2-30 字，`date` 格式 `YYYY-MM-DD HH:MM:SS +0800`

4. **图片必须与主题强相关**：写 AI 编程工具就要用代码/IDE 截图，写 AI 视频就要用视频编辑界面，不能用抽象的 `ai-brain.jpg` 之类的通用图

5. **不要编造数据**：所有价格去官网核实后再写

6. **不要写伪第一人称**："我试了一下"、"我花了一周测试" 等虚构体验直接会导致审阅不通过

7. **头条号发布前必须上传图片**：先调用 `/spice/image` 上传到头条 CDN，再替换 markdown 中的图片 URL

8. **知乎发布用 GitHub raw URL**：图片保持 `https://raw.githubusercontent.com/wk123-11/ai-tool-review/main/images/xxx.jpg`

9. **两个发布脚本的 markdown→HTML 逻辑是独立的**：如果改了 `publish_toutiao.py` 的转换逻辑，要同步改 `publish_zhihu.py`

10. **git 操作前先设置代理**：`export https_proxy=http://172.21.16.1:7890`

---

*文档结束。如需补充任何细节，请参考上方列出的 skill 文件和脚本源码。*
