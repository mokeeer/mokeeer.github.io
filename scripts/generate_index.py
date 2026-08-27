#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
扫描 briefings/ 目录下的日报 HTML，按日期倒序生成：
  1. index.html   —— 列表页（浅色扁平科技风，左侧时间轴 + 右侧论文卡片）
  2. archive.md   —— Markdown 归档单文件

用法（在项目根目录执行）:
    python scripts/generate_index.py

依赖: 仅 Python 标准库，无第三方包。
"""
import re
import sys
from datetime import datetime
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BRIEFINGS_DIR = ROOT / "briefings"
OUT_HTML = ROOT / "index.html"
OUT_MD = ROOT / "archive.md"

DATE_RE = re.compile(r"(\d{4})(\d{2})(\d{2})")


def strip_tags(s: str) -> str:
    return unescape(re.sub(r"<[^>]+>", "", s)).strip()


def collapse(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def shorten(s: str, n: int) -> str:
    s = s.strip()
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def parse_briefing(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")

    m = DATE_RE.search(path.name)
    date = datetime.strptime(m.group(0), "%Y%m%d") if m else None

    m = re.search(r"<h1>(.*?)</h1>", raw, re.S)
    title = collapse(strip_tags(m.group(1))) if m else "纳指100 全球投资要闻"

    m = re.search(r"时间窗\s*[:：]?\s*([^<（]+)", raw)
    window = m.group(1).strip() if m else ""

    m = re.search(r"新闻总数\s*[:：]?\s*(\d+)", raw)
    count = int(m.group(1)) if m else len(re.findall(r'class="tl-item', raw))

    # 来源：新版用 src-badge，旧版用 badge src
    m = re.search(r'<span class="src-badge">(.*?)</span>', raw, re.S)
    if not m:
        m = re.search(r'<span class="badge src">(.*?)</span>', raw, re.S)
    src = collapse(strip_tags(m.group(1))) if m else ""

    m = re.search(r"<h2>(.*?)</h2>", raw, re.S)
    headline = collapse(strip_tags(m.group(1))) if m else ""

    m = re.search(r'<p class="summary">(.*?)</p>', raw, re.S)
    summary = collapse(strip_tags(m.group(1))) if m else ""

    # 关注原因：新版用 .reason 结构，旧版用 .why 结构
    m = re.search(r'<div class="reason">.*?<p>(.*?)</p>', raw, re.S)
    if not m:
        m = re.search(r'<div class="why">.*?</b>(.*?)</div>', raw, re.S)
    reason = collapse(strip_tags(m.group(1))) if m else ""

    return {"date": date, "title": title, "window": window, "count": count,
            "src": src, "headline": headline, "summary": summary, "reason": reason,
            "filename": path.name}


CSS = r"""
:root{
  --bg:#f4f7fc;
  --card:#ffffff;
  --ink:#1c2b3a;
  --sub:#5b6b7c;
  --faint:#8a97a6;
  --line:#e2e9f3;
  --blue:#1f6fff;
  --blue-deep:#1250c8;
  --blue-soft:#e8f0ff;
  --blue-line:#cfe0ff;
}
*{margin:0;padding:0;box-sizing:border-box;}
html{scroll-behavior:smooth;}
body{
  background:linear-gradient(180deg,#f4f7fc 0%,#eef3fb 100%);
  color:var(--ink);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
  -webkit-font-smoothing:antialiased;
  line-height:1.6;
}

/* ===== Hero ===== */
.hero{text-align:center;padding:46px 16px 24px;}
.kicker{
  display:inline-block;font-size:12px;letter-spacing:5px;color:var(--blue);
  font-weight:700;background:var(--blue-soft);border:1px solid var(--blue-line);
  border-radius:999px;padding:5px 16px;margin-bottom:14px;
}
h1{font-size:29px;font-weight:800;letter-spacing:1px;color:var(--ink);margin-bottom:16px;}
.badges{display:flex;justify-content:center;gap:10px;flex-wrap:wrap;}
.badge{
  font-size:12.5px;font-weight:600;padding:7px 16px;border-radius:999px;
  background:var(--card);color:var(--blue);border:1px solid var(--blue-line);
  box-shadow:0 1px 4px rgba(20,60,120,.06);
  display:inline-flex;align-items:center;gap:6px;
}
.badge .dot{width:7px;height:7px;border-radius:50%;background:var(--blue);display:inline-block;}

/* ===== 时间轴 ===== */
.tl{position:relative;max-width:980px;margin:0 auto;padding:18px 16px 10px;}
.tl::before{
  content:"";position:absolute;left:93px;top:28px;bottom:40px;width:2px;
  background:linear-gradient(180deg,#1f6fff 0%,#8fb8ff 70%,#dbe7fb 100%);
  border-radius:2px;
}
.tl-item{display:grid;grid-template-columns:84px 1fr;gap:24px;margin-bottom:26px;}
.tl-marker{position:relative;text-align:right;padding-top:24px;}
.tl-time{font-size:12px;color:var(--sub);font-weight:600;font-variant-numeric:tabular-nums;line-height:1.45;}
.tl-dot{
  position:absolute;right:-7px;top:28px;width:13px;height:13px;border-radius:50%;
  background:var(--blue);border:3px solid #fff;
  box-shadow:0 0 0 2px #bcd6ff;
}

/* ===== 论文卡片 ===== */
.card{
  display:block;background:var(--card);border:1px solid var(--line);border-radius:14px;
  padding:20px 22px 18px;box-shadow:0 1px 4px rgba(20,50,100,.06);
  transition:transform .25s ease,box-shadow .25s ease;text-decoration:none;color:inherit;
}
.card:hover{transform:translateY(-3px);box-shadow:0 10px 26px rgba(20,60,130,.12);}
.card-top{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:10px;}
.num{
  font-family:"SF Mono",Consolas,Menlo,monospace;font-weight:800;font-size:12.5px;
  color:var(--blue);background:var(--blue-soft);border:1px solid var(--blue-line);
  border-radius:7px;padding:3px 9px;letter-spacing:.5px;
}
.src-badge{
  font-size:11px;font-weight:700;color:var(--blue-deep);
  background:#eef4ff;border:1px solid var(--blue-line);
  border-radius:999px;padding:3px 11px;letter-spacing:.5px;
}
.card-time{font-size:11px;color:var(--faint);margin-left:auto;font-variant-numeric:tabular-nums;}
.card h2{font-size:16.5px;font-weight:800;color:var(--ink);line-height:1.5;margin-bottom:10px;letter-spacing:.3px;}
.summary{font-size:13.5px;line-height:1.78;color:#33475c;margin-bottom:14px;text-align:justify;}
.summary b{color:#1c2b3a;}
.reason{
  background:#f6f9ff;border-left:3px solid var(--blue);
  border-radius:0 10px 10px 0;padding:12px 15px 13px;
}
.reason-label{
  display:block;font-size:11px;font-weight:800;color:var(--blue);
  letter-spacing:2px;margin-bottom:6px;
}
.reason p{margin:0;font-size:13px;line-height:1.75;color:#3d4f63;text-align:justify;}

/* ===== 底部 ===== */
footer{max-width:980px;margin:8px auto 0;padding:6px 16px 46px;}
.foot-note{font-size:12px;color:var(--faint);line-height:1.9;text-align:center;}
.disclaimer{
  font-size:12px;color:#9aa7b5;border-top:1px dashed #d3dfee;
  padding-top:14px;margin-top:12px;text-align:center;line-height:1.9;
}

/* ===== 滚动渐入 ===== */
.reveal{opacity:0;transform:translateY(26px);transition:opacity .7s ease,transform .7s ease;}
.reveal.visible{opacity:1;transform:none;}

/* ===== 响应式 ===== */
@media(max-width:760px){
  h1{font-size:22px;}
  .tl{padding:14px 12px 8px;}
  .tl::before{display:none;}
  .tl-item{grid-template-columns:1fr;gap:6px;margin-bottom:22px;}
  .tl-marker{display:none;}
  .card-time{margin-left:0;width:100%;}
  .card{padding:16px 16px 14px;}
}
"""


def build_html(items: list) -> str:
    cards = []
    for i, it in enumerate(items):
        num = f"{i + 1:02d}"
        dstr = it["date"].strftime("%Y-%m-%d") if it["date"] else "----"
        md_ = it["date"].strftime("%m-%d") if it["date"] else "--"
        yr_ = it["date"].strftime("%Y") if it["date"] else "----"
        src = it["src"] if it["src"] else "公开财经媒体"
        cards.append(f"""
  <div class="tl-item reveal">
    <div class="tl-marker"><div class="tl-time">{md_}<br>{yr_}</div><div class="tl-dot"></div></div>
    <a class="card" href="briefings/{it['filename']}">
      <div class="card-top">
        <span class="num">{num}</span>
        <span class="src-badge">{src}</span>
        <span class="card-time">{dstr} · {it['count']} 条动态</span>
      </div>
      <h2>{it['title']} · {dstr}</h2>
      <p class="summary">{shorten(it['summary'], 160)}</p>
      <div class="reason">
        <span class="reason-label">关注原因</span>
        <p>{shorten(it['reason'], 120)}</p>
      </div>
    </a>
  </div>""")

    total = len(items)
    latest = items[0]["date"].strftime("%Y-%m-%d") if items and items[0]["date"] else "—"
    earliest = items[-1]["date"].strftime("%Y-%m-%d") if items and items[-1]["date"] else "—"
    total_news = sum(i["count"] for i in items)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>纳指100 全球投资要闻 · 每日简报归档</title>
<style>{CSS}</style>
</head>
<body>

<header class="hero reveal">
  <span class="kicker">DAILY BRIEFING ARCHIVE</span>
  <h1>纳指100 全球投资要闻 · 每日简报归档</h1>
  <div class="badges">
    <span class="badge"><span class="dot"></span>时间窗 {earliest} ～ {latest}</span>
    <span class="badge"><span class="dot"></span>新闻总数 {total_news} 条</span>
    <span class="badge"><span class="dot"></span>共 {total} 期简报</span>
  </div>
</header>

<main class="tl" id="tl">{''.join(cards)}
</main>

<footer class="reveal">
  <p class="foot-note">数据来源：财联社、华尔街见闻、金十数据、上海证券报、同花顺、陆家嘴财经早餐等公开财经媒体整理，按发布时间倒序收录。</p>
  <p class="disclaimer"><b>免责声明：</b>以上内容基于公开数据和量化分析，仅供参考，不构成投资建议。市场有风险，投资需谨慎。任何投资决策应结合个人风险承受能力、资金状况和投资目标独立判断，必要时咨询持牌专业机构。过往表现不预示未来收益。</p>
</footer>

<script>
(function(){{
  var els = document.querySelectorAll('.reveal');
  if(!('IntersectionObserver' in window)){{
    for(var i=0;i<els.length;i++){{ els[i].classList.add('visible'); }}
    return;
  }}
  var io = new IntersectionObserver(function(entries){{
    for(var j=0;j<entries.length;j++){{
      var e = entries[j];
      if(e.isIntersecting){{ e.target.classList.add('visible'); io.unobserve(e.target); }}
    }}
  }}, {{ threshold: 0.1, rootMargin: '0px 0px -30px 0px' }});
  for(var k=0;k<els.length;k++){{ io.observe(els[k]); }}
}})();
</script>

</body>
</html>
"""


def build_md(items: list) -> str:
    total = len(items)
    latest = items[0]["date"].strftime("%Y-%m-%d") if items and items[0]["date"] else "—"
    earliest = items[-1]["date"].strftime("%Y-%m-%d") if items and items[-1]["date"] else "—"
    total_news = sum(i["count"] for i in items)

    lines = [
        "# 纳指100 全球投资要闻 · 每日简报归档",
        "",
        f"> 时间窗：{earliest} ～ {latest} ｜ 共 {total} 期 ｜ 新闻 {total_news} 条",
        "",
        "---",
        "",
    ]

    for i, it in enumerate(items):
        num = f"{i + 1:02d}"
        dstr = it["date"].strftime("%Y-%m-%d") if it["date"] else "----"
        src = it["src"] if it["src"] else "公开财经媒体"
        lines += [
            f"## {num} · {dstr} · {it['title']}",
            "",
            f"**来源**：{src}",
            f"**动态条数**：{it['count']} 条",
            "",
            f"**摘要**：{it['summary']}",
            "",
            f"**关注原因**：{it['reason']}",
            "",
            f"**原文**：`briefings/{it['filename']}`",
            "",
            "---",
            "",
        ]

    return "\n".join(lines).rstrip() + "\n"


def main():
    if not BRIEFINGS_DIR.exists():
        print(f"[错误] 未找到目录: {BRIEFINGS_DIR}")
        sys.exit(1)

    items = []
    for path in sorted(BRIEFINGS_DIR.glob("NASDAQ100_daily_briefing_*.html")):
        data = parse_briefing(path)
        if data["date"] is None:
            print(f"[跳过] 文件名缺少日期: {path.name}")
            continue
        items.append(data)

    if not items:
        print("[提示] briefings/ 目录下没有符合命名规则的日报文件。")
        print("       文件命名格式: NASDAQ100_daily_briefing_YYYYMMDD.html")
        sys.exit(1)

    items.sort(key=lambda x: x["date"], reverse=True)

    OUT_HTML.write_text(build_html(items), encoding="utf-8")
    print(f"[完成] 已生成 {OUT_HTML}")

    OUT_MD.write_text(build_md(items), encoding="utf-8")
    print(f"[完成] 已生成 {OUT_MD}")
    print(f"       共 {len(items)} 期简报，最新: {items[0]['date'].strftime('%Y-%m-%d')}")


if __name__ == "__main__":
    main()
