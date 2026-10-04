"""Verification gate.

Builds each workbook, recalculates it with an independent engine (`formulas`),
and compares the key outputs with a pure-Python mirror of the same maths.
A difference above Rs 0.005 (half a paisa) or 1e-6 on ratios fails the gate.

Run:  python3 verify.py      (exit code 0 = all checks pass)
"""
import os
import statistics as st
import sys
import tempfile

import build_anchor
import build_screening
import build_valuation
from calc import recalc

TOL = 0.005
results = []


def check(label, model, mirror, tol=TOL):
    ok = isinstance(model, (int, float)) and abs(model - mirror) <= tol
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {label:<55} model={model!r:<24} mirror={mirror:.6f}")


# --------------------------------------------------------------- valuation mirror
V = dict(pre_sh=8.0, esop=0.10, fresh=200, fixed=1.10, floor=180, cap=190, obj_net=170, exp=0.05, gcp=0.10,
         ipo_capex=120, y1=0.60, rev0=1000, rev_prev=850, ebitda0=150, da0=25, pat0=80, nw0=450, nd0=120,
         nwc0=200, nwc_prev=165, capex0=60, tax=0.2517, rf=0.065, beta=1.10, erp=0.07, size=0.02, csp=0.01,
         kd=0.10, dw=0.20, g=0.045, w_dcf=0.60, w=(0.40, 0.40, 0.20), disc=0.10)
SCEN = {1: dict(gr=(0.08, 0.07, 0.06, 0.06, 0.05), m=0.13, nwc=0.22, roic=0.14),
        2: dict(gr=(0.18, 0.16, 0.14, 0.12, 0.10), m=0.15, nwc=0.20, roic=0.18),
        3: dict(gr=(0.25, 0.22, 0.18, 0.15, 0.12), m=0.165, nwc=0.18, roic=0.22)}
PEERS = [(520, 5.0, 150, 290, 170, 1100), (310, 9.0, 60, 300, 160, 950), (1450, 1.5, -40, 230, 140, 800),
         (95, 30.0, 400, 420, 210, 1500)]  # included peers: cmp, shares, net debt, ebitda, pat, nw


def valuation_mirror(s):
    v, sc = V, SCEN[s]
    ke = v["rf"] + v["beta"] * v["erp"] + v["size"] + v["csp"]
    wacc = (1 - v["dw"]) * ke + v["dw"] * v["kd"] * (1 - v["tax"])
    fresh_net = v["fresh"] * (1 - v["exp"])
    ipo = 0 if s == 1 else v["ipo_capex"]
    credit = fresh_net - v["ipo_capex"] + ipo
    shares = v["pre_sh"] + v["esop"] + v["fixed"]
    da_pct = v["da0"] / v["rev0"]
    k = max(0, (v["capex0"] - v["da0"]) / (v["rev0"] - v["rev_prev"]))
    rev, nwc, pv, nopats = [v["rev0"]], v["nwc0"], 0.0, []
    for t, gr in enumerate(sc["gr"], start=1):
        r = rev[-1] * (1 + gr)
        da = r * da_pct
        nopat = (r * sc["m"] - da) * (1 - v["tax"])
        capex = da + k * (r - rev[-1]) + ipo * (v["y1"] if t == 1 else (1 - v["y1"]) if t == 2 else 0)
        new_nwc = r * sc["nwc"]
        fcf = nopat + da - capex - (new_nwc - nwc)
        pv += fcf / (1 + wacc) ** t
        rev.append(r)
        nwc = new_nwc
        nopats.append(nopat)
    g = v["g"]
    tv = nopats[-1] * (1 + g) * (1 - g / sc["roic"]) / (wacc - g)
    ev = pv + tv / (1 + wacc) ** 5
    dcf = (ev - v["nd0"] + credit) / shares
    # relative
    pe = st.median([c * sh / pat for c, sh, nd, e, pat, nw in PEERS])
    eve = st.median([(c * sh + nd) / e for c, sh, nd, e, pat, nw in PEERS])
    pb = st.median([c * sh / nw for c, sh, nd, e, pat, nw in PEERS])
    vals = [pe * v["pat0"] / shares, (eve * v["ebitda0"] - v["nd0"] + fresh_net) / shares,
            pb * (v["nw0"] + fresh_net) / shares]
    rel = sum(a * b for a, b in zip(vals, v["w"])) / sum(v["w"]) * (1 - v["disc"])
    blend = v["w_dcf"] * dcf + (1 - v["w_dcf"]) * rel
    # reverse DCF at cap
    ev_cap = v["cap"] * shares + v["nd0"] - fresh_net
    nopat0 = (v["ebitda0"] - v["da0"]) * (1 - v["tax"])
    fcf0 = nopat0 + v["da0"] - v["capex0"] - (v["nwc0"] - v["nwc_prev"])
    req_margin = ev_cap * (wacc - g) / ((1 + g) * (1 - g / sc["roic"])) / (1 - v["tax"]) / v["rev0"]
    return dict(wacc=wacc, dcf=dcf, rel=rel, blend=blend, tv_share=(tv / (1 + wacc) ** 5) / ev,
                mult=ev_cap / fcf0, req_margin=req_margin, g_impl=(ev_cap * wacc - fcf0) / (ev_cap + fcf0))


def verify_valuation(tmp):
    for s in (1, 2, 3):
        path = os.path.join(tmp, f"val_{s}.xlsx")
        A = build_valuation.build(path, scenario=s)
        x, m = recalc(path), valuation_mirror(s)
        tag = {1: "Bear", 2: "Neutral", 3: "Bull"}[s]
        wc = A["wacc"].split("!")[1].replace("$", "")
        check(f"[{tag}] WACC", x[("ASSUMPTIONS", wc)], m["wacc"], 1e-9)
        check(f"[{tag}] DCF value / share", x[("DCF", "C37")], m["dcf"])
        check(f"[{tag}] TV share of EV", x[("DCF", "C32")], m["tv_share"], 1e-9)
        check(f"[{tag}] Relative value / share", x[("RELATIVE", "F11")], m["rel"])
        check(f"[{tag}] Blended value / share", x[("SUMMARY", "C9")], m["blend"])
        check(f"[{tag}] Reverse DCF: EV / FCF at cap", x[("REVERSEDCF", "D9")], m["mult"], 1e-6)
        check(f"[{tag}] Reverse DCF: implied g at cap", x[("REVERSEDCF", "D11")], m["g_impl"], 1e-9)
        check(f"[{tag}] Reverse DCF: required EBIT margin", x[("REVERSEDCF", "D13")], m["req_margin"], 1e-9)
        check(f"[{tag}] Sensitivity grid 1 centre = DCF", x[("SENSITIVITY", "E8")], m["dcf"])
        check(f"[{tag}] Sensitivity grid 2 centre = DCF", x[("SENSITIVITY", "E16")], m["dcf"])
        print(f"       [{tag}] DCF {m['dcf']:.2f} | Rel {m['rel']:.2f} | Blend {m['blend']:.2f} | "
              f"flags: {x[('SUMMARY', 'C12')][:40]} / {x[('SUMMARY', 'C15')][:30]}")


# ------------------------------------------------------------------ anchor mirror
def verify_anchor(tmp):
    path = os.path.join(tmp, "anchor.xlsx")
    meta = build_anchor.build(path)
    x = recalc(path)
    net = 500 - 5 - 0
    anchor = net * 0.50 * 0.60
    open_pool = anchor * (1 - 1 / 3 - 0.0667)
    shares = int(min(25 * 0.60, open_pool) * 1e7 // 100)
    cost = shares * 100 / 1e7
    t1 = int(shares * 0.5)
    t2 = shares - t1
    d1, d2 = 4 + 30, 4 + 90          # pay-in 12-Oct, allotment 16-Oct
    fund = (t1 * d1 + t2 * d2) * 100 / 1e7 * 0.09 / 365
    paths = {"C": (-0.15, -0.20), "D": (0.08, 0.12), "E": (0.30, 0.40)}
    ar = meta["anchor_rows"]
    check("Anchor: open anchor pool (Rs cr)", x[("ALLOCATION", "C" + meta["alloc"]["anc_open"].split("$")[-1])],
          open_pool, 1e-9)
    check("Anchor: shares allotted", x[("ALLOCATION", "C" + meta["alloc"]["shares"].split("$")[-1])], shares, 0)
    check("Anchor: funding cost (Rs cr)", x[("ALLOCATION", "C" + meta["alloc"]["fund"].split("$")[-1])], fund, 1e-9)
    for col, (p30, p90) in paths.items():
        gross = (t1 * 100 * (1 + p30) + t2 * 100 * (1 + p90)) / 1e7
        pnl = gross * (1 - 0.0025) - cost - fund
        check(f"Anchor: net P&L col {col} (Rs cr)", x[("ALLOCATION", f"{col}{ar['pnl']}")], pnl, 1e-9)
    # overhang: anchor tranche 1 vs float at listing
    float0 = 1000 - (anchor * 100 / 100 + 150 + 300 + 200)
    f0, _ = meta["overhang_rows"]
    check("Overhang: free float at listing (lakh)", x[("OVERHANG", "C5")], float0, 1e-9)
    check("Overhang: anchor T1 release % of float", x[("OVERHANG", f"G{f0}")], anchor * 100 / 100 * 0.5 / float0, 1e-9)


# --------------------------------------------------------------- screening mirror
def verify_screening(tmp):
    path = os.path.join(tmp, "screen.xlsx")
    R, m0 = build_screening.build(path)
    x = recalc(path)
    r = m0 + 2
    check("Screen: cumulative CFO / PAT", x[("QUICK METRICS", f"C{r}")], (30 + 28 + 52) / (45 + 63 + 80), 1e-9)
    check("Screen: cumulative cash tax rate", x[("QUICK METRICS", f"C{r + 1}")], (14 + 20 + 24) / (60 + 85 + 108), 1e-9)
    check("Screen: incremental NWC per Rs revenue", x[("QUICK METRICS", f"C{r + 17}")],
          ((210 + 140 - 150) - (160 + 120 - 115)) / (1000 - 850), 1e-9)
    check("Screen: post-issue ROE", x[("QUICK METRICS", f"C{r + 19}")], 80 / (450 + 190), 1e-9)


# ------------------------------------------------------------- issuer-mode checks
def verify_issuer_mode(tmp):
    """facts.json flows through; anything not supplied stays blank (a declared gap)."""
    import json
    from openpyxl import load_workbook
    facts = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tests", "sample_facts.json")))
    p = os.path.join(tmp, "issuer_val.xlsx")
    build_valuation.build(p, scenario=2, facts=facts["valuation"])
    check("Issuer mode: Neutral DCF from facts.json", recalc(p)[("DCF", "C37")], valuation_mirror(2)["dcf"])
    p = os.path.join(tmp, "issuer_screen.xlsx")
    build_screening.build(p, facts=facts["screening"])
    q = load_workbook(p)["Quick Metrics"]
    blank_ok = q["C6"].value is None and q["F5"].value is None and q["C5"].value == 620
    results.append(blank_ok)
    print(f"{'PASS' if blank_ok else 'FAIL'}  Issuer mode: missing figures left blank, supplied kept")


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as tmp:
        print("== Valuation (all three scenarios) ==")
        verify_valuation(tmp)
        print("== Anchor & QIB ==")
        verify_anchor(tmp)
        print("== Screening ==")
        verify_screening(tmp)
        print("== Issuer mode ==")
        verify_issuer_mode(tmp)
    n, ok = len(results), sum(results)
    print(f"\n{ok}/{n} checks passed")
    sys.exit(0 if ok == n else 1)
