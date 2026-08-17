#!/usr/bin/env python3
"""读取 new_teacher.json, 发送 HTML 邮件: 发现新课：<链接>; 已发送过的课程不再重复发"""
import json
import os
import urllib.request

API = "https://mail.sunsetzhong.indevs.in/api/v1/send"
KEY = os.environ.get("MAIL_API_KEY", "")
TO = os.environ.get("MAIL_TO", "")
REPORTED = "data/reported.json"


def load_reported():
    try:
        with open(REPORTED, encoding="utf-8") as f:
            return set(json.load(f))
    except Exception:
        return set()


def save_reported(ids):
    with open(REPORTED, "w", encoding="utf-8") as f:
        json.dump(sorted(ids), f, ensure_ascii=False, indent=2)


def main():
    with open("new_teacher.json", encoding="utf-8") as f:
        courses = json.load(f)
    if not courses:
        print("无新课, 不发送")
        return
    reported = load_reported()
    fresh = [c for c in courses if str(c["course_id"]) not in reported]
    if not fresh:
        print("全部已发送过, 跳过")
        return
    lines = "".join(
        f'<p style="margin:4px 0">发现新课：'
        f'<a href="{c["url"]}" style="color:#2563eb;text-decoration:none">{c["name"]}</a></p>'
        for c in fresh
    )
    html = f'<div style="font-family:system-ui,sans-serif;font-size:15px;line-height:1.7">{lines}</div>'
    body = json.dumps({
        "to": TO,
        "subject": f"[微师] 发现新课 {len(fresh)} 门",
        "html": html,
    }).encode("utf-8")
    req = urllib.request.Request(API, data=body, headers={
        "Authorization": "Bearer " + KEY,
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        print("邮件已发送:", r.read().decode("utf-8", "replace"))
    for c in fresh:
        reported.add(str(c["course_id"]))
    save_reported(reported)


if __name__ == "__main__":
    main()