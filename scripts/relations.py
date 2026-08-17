#!/usr/bin/env python3
"""一次性: 抓取老师单课 -> 所属系列 从属关系, 输出 data/courses/course_relations.csv
列: course_id, course_name, series_id, series_name, class_id, class_name, price, start_time, learn_cnt"""
import csv
import json
import os
import urllib.request
from concurrent.futures import ThreadPoolExecutor

BASE = "https://m.weishi100.com/m/course/info"
COOKIE = os.environ.get("WEISHI_COOKIE", "")
UA = os.environ.get("WEISHI_UA", "Mozilla/5.0")
SRC = "data/courses/teacher_courses.csv"
OUT = "data/courses/course_relations.csv"
HEADER = ["course_id", "course_name", "series_id", "series_name", "class_id", "class_name",
          "price", "start_time", "learn_cnt"]


def fetch(course_id):
    url = f"{BASE}?courseId={course_id}&courseMode=1"
    req = urllib.request.Request(url, headers={"Cookie": COOKIE, "User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return course_id, r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return course_id, e.code, ""
    except Exception:
        return course_id, 0, ""


def main():
    ids = []
    with open(SRC, encoding="utf-8-sig") as f:
        for row in csv.reader(f):
            if len(row) > 2 and row[0].isdigit() and row[2] == "1":
                ids.append(row[0])
    print(f"老师单课数: {len(ids)}")
    from collections import Counter
    statuses = Counter()
    rows, sample = [], None
    with ThreadPoolExecutor(max_workers=20) as ex:
        for cid, status, body in ex.map(fetch, ids):
            statuses[status] += 1
            try:
                d = json.loads(body)
            except Exception:
                d = None
            if d and d.get("code") == 200:
                data = d.get("data") or {}
                c = data.get("course") or {}
                cr = data.get("classroom") or {}
                s = c.get("seriesCourse") or data.get("seriesCourse") or {}
                if sample is None:
                    sample = json.dumps({"courseKeys": list(c.keys()), "series": s, "classroom": cr},
                                        ensure_ascii=False)[:800]
                rows.append([
                    str(c.get("id") or cid),
                    c.get("name", ""),
                    s.get("id", ""),
                    s.get("name", ""),
                    cr.get("classId", ""),
                    cr.get("name", ""),
                    c.get("price") or "",
                    c.get("startTime") or "",
                    c.get("learnCount") or "",
                ])
    print("HTTP状态分布:", dict(statuses))
    if sample:
        print("SAMPLE:", sample)
    elif statuses:
        print("BODY样例:", statuses.most_common(1)[0])
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(HEADER)
        w.writerows(rows)
    print(f"完成: {len(rows)} 行 -> {OUT}")


if __name__ == "__main__":
    main()