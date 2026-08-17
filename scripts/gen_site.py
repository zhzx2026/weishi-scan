#!/usr/bin/env python3
"""完整重爬: 老师全部单课+系列信息、购买状态、canSellAlone, 生成 courses_data.csv + 老师课程.html"""
import csv
import datetime
import html
import json
import os
import urllib.request
from concurrent.futures import ThreadPoolExecutor


def _fmt(ms):
    return datetime.datetime.fromtimestamp(ms / 1000).strftime("%Y-%m-%d %H:%M") if ms else ""

COOKIE = os.environ["WEISHI_COOKIE"]
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 26_3_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.18 Safari/537.36"
INFO = "https://m.weishi100.com/m/course/info"
QR = "https://m.weishi100.com/m/course/v2/getPayQrCode"
CLASS_ID = "59253"


def http_get(url):
    req = urllib.request.Request(url, headers={"Cookie": COOKIE, "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def http_post(url, body):
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"Cookie": COOKIE, "User-Agent": UA,
                                          "Content-Type": "application/json",
                                          "Origin": "https://m.weishi100.com"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def fetch_info(job):
    cid, mode = job
    try:
        d = http_get(f"{INFO}?courseId={cid}&courseMode={mode}")
        return cid, mode, d
    except Exception as e:
        return cid, mode, {"code": 0, "error": str(e)}


def check_qr(job):
    cid, mode = job
    for _ in range(3):
        try:
            d = http_post(QR, {"courseId": int(cid), "courseMode": mode, "payMethod": 1})
            return cid, mode, d
        except Exception:
            continue
    return cid, mode, {"code": 0, "msg": "请求失败"}


# 1. 老师全部课程 ID (单课+系列)
ids, series_ids = [], []
with open("data/courses/teacher_courses.csv", encoding="utf-8-sig") as f:
    for r in csv.reader(f):
        if len(r) > 2 and r[0].isdigit():
            (ids if r[2] == "1" else series_ids).append(r[0])

print(f"单课 {len(ids)} 门, 系列 {len(series_ids)} 个")

# 2. 并发抓取信息
info = {}
with ThreadPoolExecutor(max_workers=20) as ex:
    for cid, mode, d in ex.map(fetch_info, [(i, 1) for i in ids] + [(i, 2) for i in series_ids]):
        if d.get("code") == 200:
            info[f"{cid}_{mode}"] = d

print(f"抓取成功: {len(info)}")

# 3. 并发检测购买状态
qr = {}
with ThreadPoolExecutor(max_workers=20) as ex:
    for cid, mode, d in ex.map(check_qr, [(i, 1) for i in ids] + [(i, 2) for i in series_ids]):
        qr[f"{cid}_{mode}"] = d

def qr_msg(cid, mode):
    d = qr.get(f"{cid}_{mode}", {})
    return d.get("code"), d.get("msg", "")

# 4. 组装数据
series_status = {}
solo = {}
rows = []
courses = []
for cid in ids:
    d = info.get(f"{cid}_1") or {}
    c = d.get("data", {}).get("course") or {}
    s = c.get("seriesCourse") or {}
    cr = d.get("data", {}).get("classroom") or {}
    cid2 = str(c.get("id") or cid)
    can = bool(c.get("canSellAlone"))
    solo[cid2] = can
    code, msg = qr_msg(cid, 1)
    if can:
        if "不可重复购买" in msg:
            buy = "已购买"
        elif "免费" in msg:
            buy = "免费"
        elif code == 200:
            buy = "可单独购买"
        else:
            buy = f"状态异常({msg})"
    else:
        buy = "不能单独购买(需随系列)"
    series_status.setdefault(str(s.get("id", "")), "正常")
    rows.append([cid2, c.get("name", ""), f"https://m.weishi100.com/mweb/single/1/?id={cid2}",
                 s.get("id", ""), s.get("name", ""), (cr.get("name", "") or "").strip(),
                 c.get("price") or "", c.get("startTime") or 0, c.get("learnCnt") or "",
                 "是" if can else "否", "", buy])
    courses.append({"id": cid2, "name": c.get("name", ""), "cover": c.get("coverUrl", ""),
                    "price": c.get("price") or "", "start": c.get("startTime") or 0,
                    "learn": c.get("learnCnt") or "", "solo": can,
                    "buy": buy, "series": {"id": s.get("id", ""), "name": s.get("name", ""),
                                           "cover": s.get("coverUrl", "")},
                    "class": {"id": cr.get("classId", ""), "name": (cr.get("name", "") or "").strip()}})

# 系列状态: 以 getPayQrCode mode=2 判定 (覆盖清单系列 + 单课父系列并集)
all_series = set(series_ids) | {str(c["series"]["id"]) for c in courses if c["series"]["id"]}
series_qr = {}
with ThreadPoolExecutor(max_workers=20) as ex:
    for sid, mode, d in ex.map(check_qr, [(i, 2) for i in sorted(all_series)]):
        series_qr[sid] = d

for sid in sorted(all_series):
    d = series_qr.get(sid, {})
    code, msg = d.get("code"), d.get("msg", "")
    if "不可重复购买" in msg:
        series_status[sid] = "已购买"
    elif "下架" in msg:
        series_status[sid] = "下架"
    elif code == 200:
        series_status[sid] = "正常"
    else:
        series_status[sid] = "状态异常"

with open("data/courses/teacher_courses.csv", "a", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    for sid in sorted(all_series - set(series_ids)):
        w.writerow([sid, "", "2", "", "59253", "", "", "", "", "", "", "", "1"])
print(f"系列检测: {len(all_series)} 个 (新增补录 {len(all_series - set(series_ids))})")

# 5. 写出 courses_data.csv (系列状态用判定后的值)
for r in rows:
    r[10] = series_status.get(str(r[3]), "正常")
with open("data/courses/courses_data.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["course_id", "course_name", "course_url", "series_id", "series_name",
                "class_name", "price", "start_time", "learn_cnt",
                "can_sell_alone", "series_status", "purchase_status"])
    for r in rows:
        r[7] = _fmt(r[7]) if isinstance(r[7], int) else r[7]
        w.writerow(r)
print(f"courses_data.csv: {len(rows)} 行")

json.dump(series_status, open("data/courses/series_status.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
json.dump(solo, open("data/courses/can_sell_alone.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)


# 6. 生成 HTML
series = {}
for c in courses:
    sid = c["series"]["id"]
    series.setdefault(sid, {"id": sid, "name": c["series"]["name"], "cover": c["series"]["cover"],
                            "courses": []})
    series[sid]["courses"].append(c)
for s in series.values():
    s["courses"].sort(key=lambda x: x["start"] or 0)
    s["latest"] = max((c["start"] for c in s["courses"]), default=0)
    s["solo_n"] = sum(1 for c in s["courses"] if c["solo"])
series_list = sorted(series.values(), key=lambda s: s["latest"], reverse=True)

def esc(x):
    return html.escape(str(x))

cards = []
for s in series_list:
    items = ""
    for c in s["courses"]:
        badge = ' <span class="cbadge">可单买</span>' if c.get("solo") else ''
        cls = '' if c.get('solo') else ' down'
        items += f"""<div class="course{cls}" data-search="{esc(c['name'])}">
          <div class="cname"><a href="https://m.weishi100.com/mweb/single/1/?id={c['id']}" target="_blank">{esc(c['name'])}</a>{badge}</div>
          <div class="cmeta">{_fmt(c['start'])}
            <span class="tag {'paid' if c['price'] else 'free'}">{('¥'+str(c['price'])) if c['price'] else '免费'}</span>
            <span class="cnt">{c['learn']}人在学</span></div>
        </div>"""
    st = series_status.get(str(s['id']), '正常')
    badge = f'<span class="sbadge {st}">{st}</span>' if st != '正常' else ''
    cards.append(f"""<div class="series{' off' if st != '正常' else ''}">
      <div class="shead">
        <div class="scover"><img loading="lazy" src="{esc(s['cover'])}" onerror="this.remove()"></div>
        <div class="sinfo">
          <a class="sname" href="https://m.weishi100.com/mweb/series/?id={s['id']}" target="_blank">{esc(s['name'])} ↗</a>
          {badge}
          <div class="smeta">{len(s['courses'])}门课 · 可单买[{s['solo_n']}/{len(s['courses'])}] · 更新至{_fmt(s['latest'])}</div>
        </div>
      </div>
      <div class="courses">{items}</div>
    </div>""")

total_paid = sum(1 for c in courses if c["price"])
down_n = sum(1 for v in series_status.values() if v == '下架')
bought_n = sum(1 for v in series_status.values() if v == '已购买')
solo_n = sum(1 for c in courses if c.get('solo'))

html_page = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>精品课程 · 课程总览</title>
<style>
body{{font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;background:#f6f7f9;margin:0;color:#222}}
header{{position:sticky;top:0;background:#fff;border-bottom:1px solid #eee;padding:14px 20px;z-index:9}}
h1{{font-size:18px;margin:0 0 6px}}
.stats{{font-size:13px;color:#888;margin-bottom:8px}}
input{{width:100%;max-width:420px;padding:8px 12px;border:1px solid #ddd;border-radius:8px;font-size:14px;outline:none}}
input:focus{{border-color:#4a90d9}}
main{{max-width:860px;margin:0 auto;padding:16px 20px 60px}}
.series{{background:#fff;border-radius:12px;margin:14px 0;padding:14px;box-shadow:0 1px 4px rgba(0,0,0,.05)}}
.shead{{display:flex;gap:12px;align-items:center}}
.scover img{{width:64px;height:64px;border-radius:8px;object-fit:cover;background:#eee}}
.sname{{font-size:16px;font-weight:600;color:#222;text-decoration:none}}
.sname:hover{{color:#4a90d9}}
.smeta{{font-size:12px;color:#888;margin-top:4px}}
.courses{{margin-top:12px}}
.course{{display:flex;justify-content:space-between;align-items:center;padding:7px 2px;border-top:1px solid #f2f2f2;gap:8px}}
.course:first-child{{border-top:none}}
.cname a{{color:#333;text-decoration:none;font-size:14px}}
.cname a:hover{{color:#4a90d9}}
.cmeta{{font-size:12px;color:#999;white-space:nowrap}}
.tag{{display:inline-block;padding:1px 7px;border-radius:10px;font-size:11px;margin-left:6px}}
.paid{{background:#fdeaea;color:#d64545}}
.free{{background:#eaf6ec;color:#3c8f4e}}
.cnt{{margin-left:6px}}
.hidden{{display:none}}
.cbadge{{display:inline-block;padding:1px 8px;border-radius:10px;font-size:11px;margin-left:6px;background:#e8f5e9;color:#2e7d32;vertical-align:2px}}
.series.off{{opacity:.55;background:#fbfbfb}}
.sbadge{{display:inline-block;padding:1px 8px;border-radius:10px;font-size:11px;margin-left:6px;vertical-align:2px}}
.sbadge.下架{{background:#fdeaea;color:#d64545}}
.sbadge.已购买{{background:#eef1f6;color:#5b6b82}}
.course.down .cname a{{color:#999;text-decoration:line-through}}
@media(max-width:600px){{.cmeta .cnt{{display:none}}}}
</style></head><body>
<header>
  <h1>{esc(courses[0]['class']['name'])}（老师 {esc(courses[0]['class']['id'])}）</h1>
  <div class="stats">共 {len(courses)} 门课 · {len(series_list)} 个系列 · 付费 {total_paid} 门 · 免费 {len(courses)-total_paid} 门 · <span style="color:#d64545">系列下架 {down_n}</span> · 已购买 {bought_n} · <span style="color:#2e7d32">可单买 {solo_n}</span>（删除线=不能单独购买）</div>
  <input id="q" placeholder="搜索课程 / 系列名..." oninput="filter()">
</header>
<main>
  <div id="seriesCount" style="font-size:12px;color:#999"></div>
  {"".join(cards)}
</main>
<script>
function filter(){{
  const q=document.getElementById('q').value.trim().toLowerCase();
  document.querySelectorAll('.series').forEach(s=>{{
    let show=s.querySelector('.sname').textContent.toLowerCase().includes(q);
    s.querySelectorAll('.course').forEach(c=>{{
      const m=c.dataset.search.toLowerCase().includes(q);
      c.classList.toggle('hidden',q&&!m&&!show);
      if(m)show=true;
    }});
    s.classList.toggle('hidden',!show);
  }});
  document.getElementById('seriesCount').textContent=
    document.querySelectorAll('.series:not(.hidden)').length+' / '+document.querySelectorAll('.series').length+' 个系列';
}}
document.getElementById('seriesCount').textContent=document.querySelectorAll('.series').length+' 个系列';
</script></body></html>"""

open('老师课程.html', 'w', encoding='utf-8').write(html_page)
print(f"OK: {len(courses)} 门课, {len(series_list)} 个系列 -> 老师课程.html")