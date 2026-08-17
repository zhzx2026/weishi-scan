#!/usr/bin/env python3
"""读取 new_teacher.json + delisted_new.json, 发送 HTML 邮件; 已发送过的课程不再重复发"""
import csv
import json
import os
import urllib.request

API = "https://mail.sunsetzhong.indevs.in/api/v1/send"
KEY = os.environ.get("MAIL_API_KEY", "")
TO = os.environ.get("MAIL_TO", "")
REPORTED = "data/reported.json"
DELISTED_NEW = "delisted_new.json"


def load_reported():
    try:
        with open(REPORTED, encoding="utf-8") as f:
            return set(json.load(f))
    except Exception:
        return set()


def save_reported(ids):
    with open(REPORTED, "w", encoding="utf-8") as f:
        json.dump(sorted(ids), f, ensure_ascii=False, indent=2)


def send(subject, html):
    body = json.dumps({"to": TO, "subject": subject, "html": html}).encode("utf-8")
    req = urllib.request.Request(API, data=body, headers={
        "Authorization": "Bearer " + KEY,
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        print("邮件已发送:", r.read().decode("utf-8", "replace"))


def main():
    parts = []

    try:
        with open(DELISTED_NEW, encoding="utf-8") as f:
            down = json.load(f)
    except Exception:
        down = []
    if down:
        names = {}
        with open("data/courses/teacher_courses.csv", encoding="utf-8-sig") as f:
            for row in csv.reader(f):
                if len(row) > 1 and row[0].isdigit():
                    names[row[0]] = row[1]
        lines = "".join(
            f'<p style="margin:4px 0">课程下架：'
            f'<a href="https://m.weishi100.com/mweb/series/?id={c}" style="color:#d64545;text-decoration:none">{names.get(c, c)}</a></p>'
            for c in down
        )
        parts.append(f'<div style="font-family:system-ui,sans-serif;font-size:15px;line-height:1.7">'
                     f'<h3 style="color:#d64545">以下课程已下架，不能购买</h3>{lines}</div>')

    try:
        with open("new_teacher.json", encoding="utf-8") as f:
            courses = json.load(f)
    except Exception:
        courses = []
    if courses:
        reported = load_reported()
        fresh = [c for c in courses if str(c["course_id"]) not in reported]
        if fresh:
            lines = "".join(
                f'<p style="margin:4px 0">发现新课：'
                f'<a href="{c["url"]}" style="color:#2563eb;text-decoration:none">{c["name"]}</a></p>'
                for c in fresh
            )
            parts.append(f'<div style="font-family:system-ui,sans-serif;font-size:15px;line-height:1.7">'
                         f'<h3 style="color:#2563eb">发现新课 {len(fresh)} 门</h3>{lines}</div>')
            for c in fresh:
                reported.add(str(c["course_id"]))
            save_reported(reported)

    if not parts:
        print("无新课、无下架, 不发送")
        return
    send(f"[微师] 新课 {len(courses)} 门 / 下架 {len(down)} 门", "".join(parts))


if __name__ == "__main__":
    main()