import sys

def main():
    start, end, group, groups, njobs, chunk = map(int, sys.argv[1:7])
    span = end - start + 1
    per = (span + groups - 1) // groups
    glo = start + group * per
    ghi = min(glo + per - 1, end)
    span2 = ghi - glo + 1
    per2 = (span2 + njobs - 1) // njobs
    lo = glo + chunk * per2
    hi = min(lo + per2 - 1, ghi)
    print(lo, hi)

main()
