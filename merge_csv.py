import csv, sys

def main():
    inp, target = sys.argv[1], sys.argv[2]
    total = teacher = 0
    with open(inp, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            total += 1
            if row.get("class_id") == target:
                teacher += 1
    print(f"总计 {total} 条课程, 其中 classId={target} 有 {teacher} 条")
    with open("out/summary.txt", "w") as f:
        f.write(f"{total} {teacher}\n")

main()
