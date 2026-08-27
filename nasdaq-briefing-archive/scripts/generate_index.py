#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
扫描 briefings/ 目录下的日报 HTML 文件，按日期倒序生成 index.html 列表页。

用法（在项目根目录执行）:
    python scripts/generate_index.py

依赖: 仅 Python 标准库，无需安装任何包。
"""
import re
import sys
from datetime import datetime
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BRIEFINGS_DIR = ROOT / "briefings"
OUTPUT = ROOT / "index.html"

DATE_RE = re.compile(r"(\d{4})(\d{2})(\d{2})")


def extract_meta(raw: str) -> dict:
    """从日报 HTML 中提取标题、副标题、新闻条数、首条新闻标题与摘要。"""
    meta = {"title": "纳斯达克100 · 每日投资动态简报", "sub": "",
            "count": 0, "headline": "", "lead": ""}

    m = re.search(r"<title>(.*?)</title>", raw, re.S)
    if m:
        meta["title"] = m.group(1).strip()

    m = re.search(r'class="sub">(.*?)</p>', raw, re.S)
    if m:
        meta["sub"] = re.sub(r"<[^>]+>", "", m.group(1)).strip()

    # 统计新闻条数：时间轴卡片数量
    meta["count"] = len(re.findall(r'class="tl-item"', raw))

    # 首条新闻：第一个 tl-card 内的标题与摘要
    card = re.search(
        r'<article class="tl-item">.*?<h2>(.*?)</h2>.*?<p class="summary">(.*?)</p>',
        raw, re.S)
    if card:
        meta["headline"] = re.sub(r"<[^>]+>", "", card.group(1)).strip()
        meta["lead"] = re.sub(r"<[^>]+>", "", card.group(2)).strip()

    return meta


def parse_briefing(path: Path):
    """解析单个日报文件 -> (日期对象, 元数据字典)。"""
    m = DATE_RE.search(path.name)
    date = datetime.strptime(f"{m.group(1)}-{m.group(2)}-{m.group(3)}", "%Y-%m-%d") if m else None
    raw = path.read_text(encoding="utf-8")
    return date, extract_meta(raw)


def shorten(text: str, limit: int = 120) -> str:
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def build_page(items: list) -> str:
    cards = []
    for date, meta, path in items:
        dstr = date.strftime("%Y-%m-%d") if date else "未知日期"
        dow = date.strftime("%A") if date else ""
        weekday_map = {"Monday": "周一", "Tuesday": "周二", "Wednesday": "周三",
                       "Thursday": "周四", "Friday": "周五",
                       "Saturday": "周六", "Sunday": "周日"}
        dow_cn = weekday_map.get(dow, "")
        headline = escape(shorten(meta["headline"], 56)) if meta["headline"] else ""
        lead = escape(shorten(meta["lead"], 140)) if meta["lead"] else ""
        title = escape(meta["title"])
        sub = escape(shorten(meta["sub"], 72)) if meta["sub"] else ""

        cards.append(f"""
    <a class="row" href="briefings/{path.name}">
      <div class="date">
        <span class="d-main">{date.strftime('%m-%d') if date else '--'}</span>
        <span class="d-year">{date.strftime('%Y') if date else '----'}</span>
        <span class="d-dow">{dow_cn}</span>
      </div>
      <div class="body">
        <div class="head">
          <h2>{title}</h2>
          <span class="count">{meta['count']} 条动态</span>
        </div>
        <p class="sub">{sub}</p>
        <p class="hl">今日焦点：{headline}</p>
        <p class="lead">{lead}</p>
      </div>
      <div class="arrow">›</div>
    </a>""")

    items_html = "\n".join(cards)
    total = len(items)
    latest = items[0][0].strftime("%Y-%m-%d") if items and items[0][0] else "—"
    earliest = items[-1][0].strftime("%Y-%m-%d") if items and items[-1][0] else "—"

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>纳斯达克100 · 每日简报归档</title>
<style>
  :root{{
    --bg:#f5f7fb; --card:#ffffff; --line:#e4eaf3;
    --ink:#1c2333; --ink-2:#5a6579; --ink-3:#8b96ab;
    --blue:#1e5ef0; --blue-2:#0ea5e9; --blue-soft:#eaf1ff;
    --radius:16px; --shadow:0 10px 30px rgba(30,58,138,.07);
  }}
  *{{margin:0;padding:0;box-sizing:border-box}}
  html{{scroll-behavior:smooth}}
  body{{
    background:var(--bg); color:var(--ink);
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
    line-height:1.65; -webkit-font-smoothing:antialiased;
  }}
  .wrap{{max-width:860px;margin:0 auto;padding:0 20px 60px}}

  .hero{{
    background:
      radial-gradient(900px 220px at 12% -40px, rgba(30,94,240,.10), transparent 60%),
      radial-gradient(700px 200px at 92% -30px, rgba(14,165,233,.10), transparent 60%),
      var(--card);
    border-bottom:1px solid var(--line);
    padding:38px 0 30px; margin-bottom:30px;
  }}
  .kicker{{font-size:12px;letter-spacing:.22em;color:var(--blue);font-weight:700;margin-bottom:10px}}
  .hero h1{{font-size:27px;font-weight:800;letter-spacing:.5px}}
  .hero .sub{{color:var(--ink-2);font-size:14px;margin-top:8px}}
  .meta-row{{display:flex;flex-wrap:wrap;gap:10px;margin-top:16px}}
  .meta-chip{{
    display:inline-flex;align-items:center;gap:6px;
    background:var(--blue-soft);color:#1443b8;border:1px solid #d3e2ff;
    font-size:12.5px;font-weight:600;padding:6px 13px;border-radius:999px;
  }}
  .meta-chip .dot{{width:7px;height:7px;border-radius:50%;background:var(--blue)}}
  .meta-chip.gray{{background:#f1f4f9;color:var(--ink-2);border-color:var(--line)}}
  .meta-chip.gray .dot{{background:var(--ink-3)}}

  .list{{display:flex;flex-direction:column;gap:14px}}
  .row{{
    display:grid;grid-template-columns:86px 1fr 28px;gap:18px;align-items:stretch;
    background:var(--card);border:1px solid var(--line);border-radius:var(--radius);
    box-shadow:var(--shadow);padding:20px 22px;text-decoration:none;color:inherit;
    transition:border-color .2s ease,transform .2s ease;
  }}
  .row:hover{{border-color:var(--blue-2);transform:translateY(-2px)}}
  .date{{
    display:flex;flex-direction:column;align-items:center;justify-content:center;
    border-right:1px solid var(--line);padding-right:18px;
  }}
  .d-main{{font-size:22px;font-weight:800;color:var(--blue);font-variant-numeric:tabular-nums}}
  .d-year{{font-size:12px;color:var(--ink-3);margin-top:1px}}
  .d-dow{{font-size:11.5px;color:var(--ink-2);background:var(--blue-soft);padding:1px 9px;border-radius:999px;margin-top:7px}}
  .head{{display:flex;align-items:center;gap:10px;flex-wrap:wrap}}
  .head h2{{font-size:16.5px;font-weight:700;line-height:1.4}}
  .count{{
    font-size:11.5px;font-weight:600;color:#1443b8;background:var(--blue-soft);
    border:1px solid #d3e2ff;padding:2px 10px;border-radius:999px;white-space:nowrap;
  }}
  .sub{{font-size:12.5px;color:var(--ink-3);margin-top:5px}}
  .hl{{font-size:13.5px;color:#333d52;margin-top:9px;font-weight:500}}
  .hl::before{{content:"★ ";color:var(--blue-2);font-size:12px}}
  .lead{{font-size:13px;color:var(--ink-2);margin-top:5px;display:-webkit-box;
    -webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}}
  .arrow{{font-size:26px;color:var(--ink-3);align-self:center;justify-self:center;font-weight:300}}
  .row:hover .arrow{{color:var(--blue-2)}}

  footer{{
    margin-top:26px;padding:22px;text-align:center;
    color:var(--ink-3);font-size:12px;background:var(--card);
    border:1px solid var(--line);border-radius:var(--radius);
  }}
  footer .line2{{margin-top:6px;color:#a9b2c4}}

  @media (max-width:640px){{
    .hero h1{{font-size:22px}}
    .row{{grid-template-columns:64px 1fr 16px;gap:12px;padding:16px}}
    .date{{padding-right:12px}}
    .d-main{{font-size:18px}}
    .head h2{{font-size:15px}}
    .lead{{-webkit-line-clamp:3}}
  }}
</style>
</head>
<body>
<div class="wrap">

  <header class="hero">
    <div class="kicker">NASDAQ-100 DAILY BRIEFING ARCHIVE</div>
    <h1>纳斯达克100 · 每日简报归档</h1>
    <p class="sub">按日期倒序收录每日投资动态简报，点击任意一天进入全文</p>
    <div class="meta-row">
      <span class="meta-chip"><span class="dot"></span>共 {total} 期简报</span>
      <span class="meta-chip gray"><span class="dot"></span>最新：{latest}</span>
      <span class="meta-chip gray"><span class="dot"></span>最早：{earliest}</span>
    </div>
  </header>

  <main class="list">{items_html}
  </main>

  <footer>
    <div>数据来源：腾讯自选股、新浪财经、华尔街见闻、证券时报、天天基金、CNBC、日经等公开资讯整理</div>
    <div class="line2">免责声明：以上内容基于公开数据和量化分析，仅供参考，不构成投资建议。市场有风险，投资需谨慎。</div>
  </footer>

</div>
</body>
</html>
"""


def main():
    if not BRIEFINGS_DIR.exists():
        print(f"[错误] 未找到目录: {BRIEFINGS_DIR}")
        sys.exit(1)

    items = []
    for path in sorted(BRIEFINGS_DIR.glob("NASDAQ100_daily_briefing_*.html")):
        date, meta = parse_briefing(path)
        if date is None:
            print(f"[跳过] 文件名缺少日期: {path.name}")
            continue
        items.append((date, meta, path))

    if not items:
        print("[提示] briefings/ 目录下没有符合命名规则的日报文件。")
        print("       文件命名格式: NASDAQ100_daily_briefing_YYYYMMDD.html")
        sys.exit(1)

    # 按日期倒序（最新在前）
    items.sort(key=lambda x: x[0], reverse=True)

    html = build_page(items)
    OUTPUT.write_text(html, encoding="utf-8")
    print(f"[完成] 已生成 {OUTPUT}")
    print(f"       共 {len(items)} 期简报，最新: {items[0][0].strftime('%Y-%m-%d')}")


if __name__ == "__main__":
    main()
