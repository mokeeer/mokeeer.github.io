# NASDAQ-100 每日简报归档站

基于 GitHub Pages 的静态归档站点模板。把你的每日日报 HTML 放入 `briefings/` 文件夹并 push，列表页（`index.html`）由脚本自动生成，按日期倒序展示。

## 目录结构

```
nasdaq-briefing-archive/
├── index.html            # 列表页（由脚本自动生成，不要手动编辑）
├── briefings/            # 每日日报 HTML 存放目录
│   └── NASDAQ100_daily_briefing_YYYYMMDD.html
├── scripts/
│   └── generate_index.py # 扫描 briefings/ 生成列表页
└── .github/workflows/
    └── deploy.yml        # push 后自动构建 + 部署到 GitHub Pages
```

## 使用方式

### 1. 创建 GitHub 仓库并推送

在 GitHub 上新建一个仓库（任意名字），然后：

```bash
cd nasdaq-briefing-archive
git init
git add .
git commit -m "init briefing archive"
git branch -M main
git remote add origin https://github.com/<你的用户名>/<仓库名>.git
git push -u origin main
```

### 2. 启用 GitHub Pages

仓库页面 → **Settings** → **Pages** → **Source** 选择 **GitHub Actions**（不是 Deploy from a branch）→ Save。首次部署约 1-2 分钟，之后每次 push 自动更新。

访问地址：`https://<你的用户名>.github.io/<仓库名>/`（仓库名非 `用户名.github.io` 时带子路径）。

### 3. 每日更新

把当天日报文件放入 `briefings/` 文件夹，命名规则保持：

```
NASDAQ100_daily_briefing_YYYYMMDD.html
```

然后推送：

```bash
git add briefings/
git commit -m "add briefing 2026-08-22"
git push
```

push 后 GitHub Actions 自动运行脚本 → 重新生成 `index.html` → 发布。列表页自动按日期倒序排列，无需任何手动操作。

## 本地预览

```bash
# 需要 Python 3.8+
python scripts/generate_index.py
# 然后直接用浏览器打开 index.html
```

## 注意事项

- **文件命名必须含日期**（`YYYYMMDD`），脚本依赖它排序；不符合命名规则的文件会被跳过。
- 列表页从每篇日报中自动提取：日期、标题、副标题、新闻条数、首条新闻标题与摘要预览。
- 仓库默认公开，不要存放敏感信息。
- 若想绑定自定义域名，在 Settings → Pages 中配置，并参考 GitHub 官方文档添加 DNS 记录。
