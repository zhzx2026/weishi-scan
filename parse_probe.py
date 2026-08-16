import sys, json

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
    cr = data.get("classroom") or {}
    c = data.get("course") or {}
    cid_num = cr.get("classId")
    if cid_num is None:
        return
    if int(cid_num) != target:
        return
    print(f"{cid} | {c.get('name')} | classId={cid_num} | mode={c.get('courseMode')} | live={c.get('liveStatus')}")

main()
