# AI工具派

精选AI工具评测、效率方法、副业赚钱思路 — 每天更新。

## 技术栈

- 静态站点生成：Jekyll + GitHub Pages
- 内容生成：AI 自动选题、研究、写作
- 部署：GitHub Actions 自动构建

## 本地开发

```bash
# 安装依赖
gem install jekyll jekyll-seo-tag jekyll-sitemap

# 启动本地服务
jekyll serve --watch
```

## 目录结构

```
├── _config.yml          # Jekyll 配置
├── _layouts/            # 页面模板
│   ├── default.html     # 默认布局
│   └── post.html        # 文章布局
├── _posts/              # 文章目录（自动生成）
├── assets/css/          # 样式
├── about/               # 关于页
├── scripts/             # 工具脚本
│   ├── generate_post.py # 内容生成器
│   └── deploy.py        # 部署脚本
└── index.html           # 首页
```
