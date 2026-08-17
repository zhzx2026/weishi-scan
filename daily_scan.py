#!/usr/bin/env python3
"""每日增量扫描: 检查 [基线+1, 基线+window] 区间的单课/系列, 收集指定老师(classId)的新课"""
import csv
import json
import os
import urllib.request
from concurrent.futures import ThreadPoolExecutor

BASE = "https://m.weishi100.com/m/course/info"
COOKIE = os.environ.get("WEISHI_COOKIE", "")
UA = os.environ.get("WEISHI_UA", "Mozilla/5.0")
TEACHER = os.environ.get("TARGET_CLASS", "59253")
HEADER = ["course_id", "name", "course_mode", "live_status", "class_id", "classroom_name",
          "publish_status", "have_permission", "price", "start_time", "learn_cnt", "cover_url", "is_target"]
NEW_CSV = "data/courses/all_courses_new.csv"


def fetch(course_id, mode):
    url = f"{BASE}?courseId={course_id}&courseMode={mode}"
    req = urllib.request.Request(url, headers={"Cookie": COOKIE, "User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return course_id, mode, r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return course_id, mode, e.code, ""
    except Exception:
        return course_id, mode, 0, ""


def main():
    with open("data/baseline.json", encoding="utf-8") as f:
        base = json.load(f)
    window = int(base.get("window", 500))
    ranges = [
        (base["lesson_max"] + 1, base["lesson_max"] + window, 1),
        (base["series_max"] + 1, base["series_max"] + window, 2),
    ]
    new_teacher, new_all, n_ok, n_401 = [], [], 0, 0
    for lo, hi, mode in ranges:
        with ThreadPoolExecutor(max_workers=20) as ex:
            for cid, m, status, body in ex.map(lambda i: fetch(i, mode), range(lo, hi + 1)):
                if status == 200:
                    n_ok += 1
                    try:
                        d = json.loads(body)
                    except Exception:
                        continue
                    if str(d.get("classId", "")) == TEACHER:
                        new_teacher.append({
                            "course_id": cid,
                            "name": d.get("name", ""),
                            "course_mode": m,
                            "price": d.get("price"),
                            "start_time": d.get("startTime"),
                            "learn_cnt": d.get("learnCount"),
                            "url": f"https://m.weishi100.com/mweb/series/?id={cid}" if m == 2
                                   else f"https://m.weishi100.com/mweb/course/?id={cid}",
                        })
                    new_all.append([
                        cid,
                        d.get("name", ""),
                        m,
                        d.get("liveStatus", ""),
                        d.get("classId", ""),
                        d.get("classroomName", ""),
                        d.get("publishStatus", ""),
                        d.get("havePermission", ""),
                        d.get("price", ""),
                        d.get("startTime", ""),
                        d.get("learnCount", ""),
                        d.get("coverUrl", ""),
                        "1" if str(d.get("classId", "")) == TEACHER else "0",
                    ])
                elif status == 401:
                    n_401 += 1
    if n_401 > 50:
        raise RuntimeError(f"疑似 cookie 失效: 401 x {n_401}, 请更新 WEISHI_COOKIE")
    base["lesson_max"] += window
    base["series_max"] += window
    with open("data/baseline.json", "w", encoding="utf-8") as f:
        json.dump(base, f, ensure_ascii=False, indent=2)
    if new_all:
        if not os.path.exists(NEW_CSV):
            with open(NEW_CSV, "w", encoding="utf-8", newline="") as f:
                csv.writer(f).writerow(HEADER)
        with open(NEW_CSV, "a", encoding="utf-8", newline="") as f:
            csv.writer(f).writerows(new_all)
    if new_teacher:
        with open("new_teacher.json", "w", encoding="utf-8") as f:
            json.dump(new_teacher, f, ensure_ascii=False, indent=2)
    print(f"扫描完成: 有效响应 {n_ok}, 401 x {n_401}, 老师新课 {len(new_teacher)} 门, 全部新课 {len(new_all)} 门")
    for t in new_teacher:
        print("  ", t["course_id"], t["name"])


if __name__ == "__main__":
    main()