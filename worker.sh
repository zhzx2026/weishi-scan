#!/bin/bash
# 单个 ID 探测 worker（GitHub Actions / 本地通用）
# 环境变量: COOKIE UA MODE TARGET WORK
# 参数: worker.sh <courseId>
id="$1"
curl -s --max-time 15 --retry 2 --retry-delay 1 \
    -H "Cookie: $COOKIE" \
    -H "User-Agent: $UA" \
    -H "Referer: https://m.weishi100.com/mweb/" \
    "https://m.weishi100.com/m/course/info?courseId=$id&courseMode=$MODE" 2>/dev/null \
    > "$WORK/probe_$id.json"
python3 "$SCRIPT_DIR/parse_probe.py" "$id" "$WORK/probe_$id.json" "$TARGET"
rm -f "$WORK/probe_$id.json"
