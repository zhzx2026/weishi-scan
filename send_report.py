#!/usr/bin/env python3
"""读取 new_teacher.json, 发送 HTML 邮件报告"""
import json
import os
import urllib.request

API = "https://mail.sunsetzhong.indevs.in/api/v1/send"
KEY = os.environ.get("MAIL_API_KEY", "")
TO = os.environ.get("MAIL_TO", "")


def main():
    with open("new_teacher.json", encoding="utf-8") as f:
        courses = json.load(f)
    if not courses:
        print("无新课, 不发送")
        return
    rows = "".join(
        f'<tr><td>{c["course_id"]}</td>'
        f'<td><a href="{c["url"]}">{c["name"]}</a></td>'
        f'<td>{"系列" if c["course_mode"] == 2 else "单课"}</td>'
        f'<td>{c.get("price") or ""}</td>'
        f'<td>{c.get("start_time") or ""}</td>'
        f'<td>{c.get("learn_cnt") or ""}</td></tr>'
        for c in courses
    )
    html = (
        '<div style="font-family:system-ui,sans-serif">'
        f'<h3>微师老师新课 {len(courses)} 门</h3>'
        '<table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse;font-size:14px">'
        "<tr><th>课程ID</th><th>课程名</th><th>类型</th><th>价格</th><th>开课时间</th><th>学习人数</th></tr>"
        f"{rows}</table></div>"
    )
    body = json.dumps({
        "to": TO,
        "subject": f"[微师] 老师新课 {len(courses)} 门",
        "html": html,
    }).encode("utf-8")
    req = urllib.request.Request(API, data=body, headers={
        "Authorization": "Bearer " + KEY,
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        print("邮件已发送:", r.read().decode("utf-8", "replace"))


if __name__ == "__main__":
    main()