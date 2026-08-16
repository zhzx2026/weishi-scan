#!/bin/bash
# 合并所有组 CSV: 等待全部 run 完成 -> 下载所有 artifact -> 合并去重 -> 输出
# 用法: ./merge_all.sh [输出目录, 默认当前目录]
set -u
cd "$(dirname "$0")"
LOG=/var/folders/5l/473n6lcx3_qf8yth_5t1ls3c0000gn/T/opencode/groups_log.txt
OUT="${1:-.}"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# 1. 等待所有 run 完成
echo "=== 等待所有 run 完成 ==="
RIDS=()
while IFS= read -r line; do
  [ -n "$line" ] || continue
  g=${line%% *}; rid=${line##* }
  RIDS+=("$rid")
done < "$LOG"
TOTAL=${#RIDS[@]}
echo "共 $TOTAL 个 run"
done_c=0
while :; do
  done_c=0
  for rid in "${RIDS[@]}"; do
    st=$(gh run view "$rid" --json status 2>/dev/null | python3 -c "import sys,json;print(json.load(sys.stdin)['status'])" 2>/dev/null)
    [ "$st" = "completed" ] && done_c=$((done_c+1))
  done
  echo "[$(date +%H:%M)] 完成 $done_c/$TOTAL ..."
  [ "$done_c" -eq "$TOTAL" ] && break
  sleep 120
done

# 2. 下载所有 artifact
echo "=== 下载所有 artifact ==="
mkdir -p "$WORK/all"
for rid in "${RIDS[@]}"; do
  gh run download "$rid" -D "$WORK/all" 2>/dev/null || echo "  run $rid 下载失败"
done
echo "下载文件数: $(find "$WORK/all" -name '*.csv' | wc -l)"

# 3. 合并去重 (按 course_id, 保留全部列, 不丢数据)
echo "=== 合并去重 ==="
mkdir -p "$OUT"
python3 - "$WORK/all" "$OUT" <<'PY'
import sys, csv, glob, os
srcdir, outdir = sys.argv[1], sys.argv[2]
files = sorted(glob.glob(os.path.join(srcdir, "**", "g*_m*.csv"), recursive=True))
print(f"读取 {len(files)} 个分片文件")
seen = {}
for f in files:
    with open(f, encoding="utf-8", errors="replace") as fh:
        for row in csv.reader(fh):
            if len(row) < 13:
                continue
            cid = row[0]
            seen.setdefault(cid, row)
rows = sorted(seen.values(), key=lambda r: int(r[0]))
header = ["course_id","name","course_mode","live_status","class_id","classroom_name",
          "publish_status","have_permission","price","start_time","learn_cnt","cover_url","is_target"]
with open(os.path.join(outdir, "all_courses.csv"), "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(header)
    w.writerows(rows)
teacher = [r for r in rows if r[4] == "59253"]
with open(os.path.join(outdir, "teacher_courses.csv"), "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(header)
    w.writerows(teacher)
total = len(rows)
print(f"全部课程: {total} 条")
print(f"老师课程(classId=59253): {len(teacher)} 条")
print(f"输出: {outdir}/all_courses.csv, {outdir}/teacher_courses.csv")
PY
