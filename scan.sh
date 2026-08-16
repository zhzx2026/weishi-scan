#!/bin/bash
# 扫描 courseMode=$1 的 courseId 区间 [$2,$3]，找出 classroom.classId==$4 的课程
# 并发线程数 $5（默认 30）
# 用法: scan.sh <mode> <start> <end> <targetClassId> [threads]
# Cookie 从环境变量 WEISHI_COOKIE / WEISHI_UA 读取（GitHub Actions 用 secrets 注入）；
# 若未设置则用下面的本地默认值。
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

if [ -n "${WEISHI_COOKIE:-}" ]; then
    COOKIE="$WEISHI_COOKIE"
else
    COOKIE='GID=e235d7c00aba87824808e9fc3bc5d6d6; weishi_login_target="https://m.weishi100.com/cweb/#/student"; _const_weishi_id_="9deceea7-bddc-45bf-ba26-d6ea804dc480::703BECE7963F4EB60DFDF01DC96A95D5"; Hm_lvt_4fe36727dba7aabcdd581120c42af358=1786059816,1786067047,1786147845,1786153870'
fi
if [ -n "${WEISHI_UA:-}" ]; then
    UA="$WEISHI_UA"
else
    UA='Mozilla/5.0 (Macintosh; Intel Mac OS X 26_3_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.18 Safari/537.36'
fi

MODE="$1"; TARGET="$4"; THREADS="${5:-30}"
export COOKIE UA MODE TARGET WORK SCRIPT_DIR
export WORK="$WORK"
python3 -c "import sys; [print(i) for i in range(int(sys.argv[1]), int(sys.argv[2])+1)]" "$2" "$3" \
  | xargs -P "$THREADS" -I{} "$SCRIPT_DIR/worker.sh" {}
echo "[DONE] mode=$MODE $2-$3" >&2
