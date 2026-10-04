"""Recalculate a workbook with the `formulas` engine and return {(sheet, cell): value}."""
import re, sys, warnings
warnings.filterwarnings("ignore")
import formulas

def recalc(path):
    sol = formulas.ExcelModel().loads(path).finish().calculate()
    out = {}
    for k, v in sol.items():
        m = re.match(r"'\[[^\]]+\](.+)'!([A-Z]+\d+)$", str(k))
        if not m:
            continue
        try:
            val = v.value[0][0]
        except Exception:
            val = v
        out[(m.group(1).upper(), m.group(2))] = val
    return out

if __name__ == "__main__":
    res = recalc(sys.argv[1])
    sheets = sys.argv[2:] or None
    for (s, c), v in sorted(res.items(), key=lambda kv: (kv[0][0], int(re.sub(r"\D", "", kv[0][1])), kv[0][1])):
        if sheets is None or s in [x.upper() for x in sheets]:
            if not isinstance(v, str) or len(v) < 120:
                print(s, c, v)
