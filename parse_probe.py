import sys, json, csv, io
from datetime import datetime, timezone, timedelta

# CSV 列: 全部现存课程都记录, is_target 标记目标班级
HEADER = ["course_id", "name", "course_mode", "live_status", "class_id", "classroom_name",
          "publish_status", "have_permission", "price", "start_time", "learn_cnt",
          "cover_url", "is_target"]

BEIJING = timezone(timedelta(hours=8))

def fmt_time(ms):
    if not ms:
        return ""
    try:
        return datetime.fromtimestamp(int(ms) / 1000, BEIJING).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(ms)

def main():
    cid, path, target = sys.argv[1], sys.argv[2], int(sys.argv[3])
    try:
        with open(path) as f:
            d = json.load(f)
    except Exception:
        return
    if d.get("code") != 200:
        return
    data = d.get("data") or {}
    c = data.get("course") or {}
    cr = data.get("classroom") or {}
    class_id = cr.get("classId")
    row = [
        str(c.get("id") or cid),
        c.get("name") or "",
        c.get("courseMode") or "",
        c.get("liveStatus") or "",
        class_id or "",
        cr.get("name") or "",
        c.get("publishStatus") or "",
        c.get("havePermission") or "",
        c.get("price") or "",
        fmt_time(c.get("startTime")),
        c.get("learnCnt") or "",
        c.get("coverUrl") or "",
        "1" if class_id is not None and int(class_id) == target else "0",
    ]
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(row)
    print(buf.getvalue().rstrip("\n"))

main()
