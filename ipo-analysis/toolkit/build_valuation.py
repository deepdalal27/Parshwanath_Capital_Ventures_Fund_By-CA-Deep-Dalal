"""Workbook 03 - Peer comps & valuation.

DCF (CAPM WACC, terminal reinvestment = g / ROIC) and relative valuation shown
separately, then blended 60:40 (editable). Reverse DCF on four levers, two
sensitivity grids, and the three degeneracy guards.

Units: Rs crore; share counts in crore, so value / shares = Rs per share.
All sample values are ILLUSTRATIVE. Replace every blue cell from the offer document.
"""
from openpyxl import Workbook

from house import (finalize, sample_banner, CR, DISCLAIMER, F_BOLD, F_NOTE, PCT, X, InputBlock, dropdown, flag_text, footer,
                   header, note, put, title, widths)

YRS = "DEFGH"  # Y1..Y5 columns on DCF


VAL_POLICY = {"basis", "tax", "rf", "beta", "erp", "size", "csp", "kd", "dw", "g", "w_dcf", "w_pe", "w_eve", "w_pb",
              "rel_disc", "capex_y1"}


def build(path, scenario=2, facts=None):
    """facts=None builds the illustrative template; facts=dict (see FACTS_SCHEMA.md) builds an issuer."""
    wb = Workbook()
    cv = wb.active
    cv.title = "Cover"
    title(cv, "Peer Comps & Valuation Model")
    for i, t in enumerate([
        "Sheets: Assumptions (only input sheet) > Peers > Relative > DCF > ReverseDCF > Sensitivity > Summary.",
        "Scenario toggle: Assumptions!C5 (1 = Bear, 2 = Neutral, 3 = Bull). Every driver needs a rationale and page cite.",
        "DCF and relative values are shown separately, then blended (default 60:40; use 80:20 if no listed peers).",
        "Terminal growth 4.50%. Capex = D&A + k x change in revenue. Terminal reinvestment = g / terminal ROIC.",
        "Bear case excludes the IPO-funded capex object AND its funding. Share count is post-issue, fully diluted.",
        "Peer multiples: P/E, EV/EBITDA, P/B. EV/Sales is deliberately excluded.",
        "Match peers on business model before industry code, and on the same basis (consolidated / standalone).",
        "Upside is reported as % only. Grey market premium never moves fair value.",
        "",
        "Colours: blue = input | black = formula | green = link | yellow = key cell.",
        sample_banner(facts),
        "", DISCLAIMER]):
        cv[f"A{i + 4}"] = t
    cv["A14"].font = F_BOLD
    cv["A16"].font = F_BOLD
    widths(cv, {"A": 120})

    # ------------------------------------------------------------ Assumptions
    ws = wb.create_sheet("Assumptions")
    title(ws, "Assumptions - the only input sheet")
    ws["B5"] = "Scenario (1 = Bear, 2 = Neutral, 3 = Bull)"
    ws["B5"].font = F_BOLD
    put(ws, "C5", scenario, "input", "0", key=True)
    put(ws, "D5", '=CHOOSE($C$5,"Bear","Neutral","Bull")', "calc")
    S = "Assumptions!$C$5"
    b = InputBlock(ws, 6, facts=None if facts is None else facts.get("inputs", {}), policy=VAL_POLICY)
    b.section("Issuer and offer")
    b.add("name", "Issuer", "Illustrative Co. Ltd (REPLACE)", None)
    b.add("basis", "Financial basis", "Consolidated", None, hint="Use the same basis for every peer")
    dropdown(ws, b.addr["basis"].split("!")[1].replace("$", ""), ["Consolidated", "Standalone"])
    b.add("pre_sh", "Pre-issue shares, fully diluted (post any bonus)", 8.00, unit="crore",
          hint="Check bonus restatement (forensic check 1)")
    b.add("esop", "ESOP / convertibles outstanding", 0.10, unit="crore")
    b.add("fresh", "Fresh issue amount (fixed at objects need)", 200, unit="Rs cr")
    b.add("fresh_sh_fixed", "Fresh shares fixed in DRHP (0 if amount-based)", 1.10, unit="crore")
    b.add("ofs_sh", "OFS shares (no effect on share count)", 2.00, unit="crore")
    b.add("floor", "Price band - floor", 180, unit="Rs")
    b.add("cap", "Price band - cap", 190, unit="Rs")
    b.add("ref", "Valuation reference price", f"={b.addr['cap']}", kind="calc", unit="Rs",
          hint="Defaults to cap; overwrite if needed")
    b.add("obj_net", "Specific objects (excl. GCP and offer expenses)", 170, unit="Rs cr")
    b.add("exp_pct", "Offer expenses as % of fresh issue", 0.05, PCT)
    b.add("gcp_pct", "GCP as % of fresh issue", 0.10, PCT, hint="Check against regulatory cap")
    b.add("ipo_capex", "IPO-funded capex object", 120, unit="Rs cr")
    b.add("capex_y1", "Share of IPO capex spent in Y1 (rest in Y2)", 0.60, PCT)
    b.section("Latest audited year (restated) - never annualise a stub")
    b.add("rev0", "Revenue from operations", 1000, unit="Rs cr")
    b.add("rev_prev", "Revenue - prior year", 850, unit="Rs cr")
    b.add("ebitda0", "EBITDA (ties to issuer KPI table)", 150, unit="Rs cr")
    b.add("da0", "Depreciation & amortisation", 25, unit="Rs cr")
    b.add("pat0", "PAT", 80, unit="Rs cr")
    b.add("nw0", "Net worth (pre-issue)", 450, unit="Rs cr")
    b.add("nd0", "Net debt (borrowings - cash)", 120, unit="Rs cr")
    b.add("nwc0", "Net working capital", 200, unit="Rs cr", hint="Reconcile to Objects-chapter WC table")
    b.add("nwc_prev", "Net working capital - prior year", 165, unit="Rs cr")
    b.add("capex0", "Capex (purchase of PPE + intangibles)", 60, unit="Rs cr")
    b.add("tax", "Tax rate", 0.2517, PCT)
    b.section("Cost of capital (CAPM build-up)")
    b.add("rf", "Risk-free rate (10y G-sec)", 0.065, PCT)
    b.add("beta", "Beta", 1.10, "0.00")
    b.add("erp", "Equity risk premium", 0.07, PCT)
    b.add("size", "Size premium", 0.02, PCT)
    b.add("csp", "Company-specific premium", 0.01, PCT)
    b.add("kd", "Pre-tax cost of debt", 0.10, PCT)
    b.add("dw", "Target debt / (debt + equity)", 0.20, PCT)
    b.add("g", "Terminal growth", 0.045, PCT)
    b.section("Blend and relative settings")
    b.add("w_dcf", "DCF weight in blend", 0.60, PCT, hint="80% where no comparable listed peers")
    b.add("w_pe", "Relative weight - P/E", 0.40, PCT)
    b.add("w_eve", "Relative weight - EV/EBITDA", 0.40, PCT)
    b.add("w_pb", "Relative weight - P/B", 0.20, PCT)
    b.add("rel_disc", "Discount to peer median", 0.10, PCT, hint="Size, liquidity, business-model gap - state why")
    b.section("Derived (formulas)")
    A = b.addr
    b.add("fresh_net", "Fresh issue net of offer expenses", f"={A['fresh']}*(1-{A['exp_pct']})", CR, "calc", "Rs cr")
    b.add("post_sh", "Post-issue diluted shares at reference price",
          f"={A['pre_sh']}+{A['esop']}+IF({A['fresh_sh_fixed']}>0,{A['fresh_sh_fixed']},{A['fresh']}/{A['ref']})",
          CR, "calc", "crore")
    b.add("ipo_used", "IPO capex used in this scenario", f"=IF({S}=1,0,{A['ipo_capex']})", CR, "calc", "Rs cr",
          hint="Bear: undersubscribed issue does not fund the project")
    b.add("proc_credit", "Proceeds credited in EV-to-equity bridge",
          f"={A['fresh_net']}-{A['ipo_capex']}+{A['ipo_used']}", CR, "calc", "Rs cr",
          hint="Bear excludes the capex object and its funding")
    b.add("ke", "Cost of equity", f"={A['rf']}+{A['beta']}*{A['erp']}+{A['size']}+{A['csp']}", PCT, "calc")
    b.add("wacc", "WACC", f"=(1-{A['dw']})*{A['ke']}+{A['dw']}*{A['kd']}*(1-{A['tax']})", PCT, "calc", key_cell=True)
    b.add("da_pct", "D&A % of revenue (latest actual)", f"={A['da0']}/{A['rev0']}", PCT, "calc")
    b.add("k", "Growth capex per Rs of incremental revenue (k)",
          f"=MAX(0,({A['capex0']}-{A['da0']})/({A['rev0']}-{A['rev_prev']}))", "0.000", "calc",
          hint="Implied from latest actual year")
    b.add("obj_floor", "Objects floor price",
          f'=IF({A["fresh_sh_fixed"]}>0,{A["obj_net"]}/(1-{A["exp_pct"]}-{A["gcp_pct"]})/{A["fresh_sh_fixed"]},"n.a.")',
          CR, "calc", "Rs", hint="Funding need / fixed fresh shares (forensic check 5)")
    A = b.addr

    # scenario drivers
    r0 = b.row + 1
    ws[f"B{r0}"] = "Scenario drivers"
    ws[f"B{r0}"].font = F_BOLD
    header(ws, r0 + 1, ["Driver", "Selected", "", "Bear", "Neutral", "Bull", "Rationale + page cite"], col=2)
    drivers = [("g1", "Revenue growth Y1", (0.08, 0.18, 0.25)), ("g2", "Revenue growth Y2", (0.07, 0.16, 0.22)),
               ("g3", "Revenue growth Y3", (0.06, 0.14, 0.18)), ("g4", "Revenue growth Y4", (0.06, 0.12, 0.15)),
               ("g5", "Revenue growth Y5", (0.05, 0.10, 0.12)), ("m", "EBITDA margin Y1-Y5", (0.13, 0.15, 0.165)),
               ("nwc", "Net working capital % revenue", (0.22, 0.20, 0.18)),
               ("roic", "Terminal ROIC", (0.14, 0.18, 0.22))]
    for i, (k, lab, vals) in enumerate(drivers):
        r = r0 + 2 + i
        if facts is not None:
            vals = tuple(facts.get("drivers", {}).get(k, (None, None, None)))
        ws[f"B{r}"] = lab
        for j, v in enumerate(vals):
            put(ws, f"{'EFG'[j]}{r}", v, "input", PCT)
        put(ws, f"C{r}", f"=INDEX(E{r}:G{r},{S})", "calc", PCT, key=True)
        put(ws, f"H{r}", "[rationale + RHP page]" if facts is None else
            facts.get("rationale", {}).get(k, "[rationale + page]"), "input")
        A[k] = f"Assumptions!$C${r}"
    widths(ws, {"A": 2, "B": 50, "C": 30, "D": 10, "E": 14, "F": 14, "G": 14, "H": 44})
    footer(ws)

    # ------------------------------------------------------------------ DCF
    d = wb.create_sheet("DCF")
    title(d, "Discounted cash flow (FCFF) - selected scenario")
    put(d, "B3", '="Scenario: "&Assumptions!$D$5', "link")
    header(d, 5, ["Rs cr", "Y0 (actual)", "Y1", "Y2", "Y3", "Y4", "Y5"], col=2)
    lab = {6: "Revenue growth", 7: "Revenue", 8: "EBITDA margin", 9: "EBITDA", 10: "D&A", 11: "EBIT",
           12: "Tax on EBIT", 13: "NOPAT", 14: "Organic capex (D&A + k x dRev)", 15: "IPO-funded capex",
           16: "Net working capital", 17: "Change in NWC", 18: "Free cash flow to firm", 19: "Discount factor",
           20: "PV of FCFF"}
    for r, t in lab.items():
        d[f"B{r}"] = t
    put(d, "C6", f"={A['rev0']}/{A['rev_prev']}-1", "link", PCT)
    put(d, "C7", f"={A['rev0']}", "link", CR)
    put(d, "C8", f"={A['ebitda0']}/{A['rev0']}", "link", PCT)
    put(d, "C9", f"={A['ebitda0']}", "link", CR)
    put(d, "C10", f"={A['da0']}", "link", CR)
    put(d, "C14", f"={A['capex0']}", "link", CR)
    put(d, "C15", 0, "calc", CR)
    put(d, "C16", f"={A['nwc0']}", "link", CR)
    put(d, "C17", f"={A['nwc0']}-{A['nwc_prev']}", "link", CR)
    for i, c in enumerate(YRS):
        p = "CDEFG"[i]
        put(d, f"{c}6", f"={A['g' + str(i + 1)]}", "link", PCT)
        put(d, f"{c}7", f"={p}7*(1+{c}6)", "calc", CR)
        put(d, f"{c}8", f"={A['m']}", "link", PCT)
        put(d, f"{c}9", f"={c}7*{c}8", "calc", CR)
        put(d, f"{c}10", f"={c}7*{A['da_pct']}", "calc", CR)
        put(d, f"{c}14", f"={c}10+{A['k']}*({c}7-{p}7)", "calc", CR)
        split = A['capex_y1'] if i == 0 else f"(1-{A['capex_y1']})" if i == 1 else "0"
        put(d, f"{c}15", f"={A['ipo_used']}*{split}", "calc", CR)
        put(d, f"{c}16", f"={c}7*{A['nwc']}", "calc", CR)
        put(d, f"{c}17", f"={c}16-{p}16", "calc", CR)
        put(d, f"{c}19", f"=1/(1+{A['wacc']})^{i + 1}", "calc", "0.0000")
        put(d, f"{c}20", f"={c}18*{c}19", "calc", CR)
    for c in "C" + YRS:
        put(d, f"{c}11", f"={c}9-{c}10", "calc", CR)
        put(d, f"{c}12", f"={c}11*{A['tax']}", "calc", CR)
        put(d, f"{c}13", f"={c}11-{c}12", "calc", CR)
        put(d, f"{c}18", f"={c}13+{c}10-{c}14-{c}15-{c}17", "calc", CR)
    tv = [
        (22, "Terminal growth (g)", f"={A['g']}", PCT),
        (23, "Terminal ROIC", f"={A['roic']}", PCT),
        (24, "Terminal reinvestment rate (g / ROIC)", "=C22/C23", PCT),
        (25, "NOPAT Y6", "=H13*(1+C22)", CR),
        (26, "FCFF Y6", "=C25*(1-C24)", CR),
        (27, "Terminal value at Y5", f"=C26/({A['wacc']}-C22)", CR),
        (28, "PV of terminal value", "=C27*H19", CR),
        (30, "Sum of PV, explicit period", "=SUM(D20:H20)", CR),
        (31, "Enterprise value", "=C30+C28", CR),
        (32, "Terminal value share of EV", "=C28/C31", PCT),
        (33, "Less: net debt", f"=-{A['nd0']}", CR),
        (34, "Add: issue proceeds credited", f"={A['proc_credit']}", CR),
        (35, "Equity value", "=C31+C33+C34", CR),
        (36, "Post-issue diluted shares (crore)", f"={A['post_sh']}", CR),
        (37, "DCF value per share (Rs)", "=C35/C36", CR),
    ]
    for r, t, f, fmt in tv:
        d[f"B{r}"] = t
        put(d, f"C{r}", f, "calc", fmt, key=(r == 37))
    d["B39"] = "Degeneracy guards"
    d["B39"].font = F_BOLD
    guards = [
        (40, "Terminal value share", '=IF(C32>1,"DEGENERATE: TV above 100% of EV - fix assumptions, do not report",'
                                     'IF(C32>0.75,"AMBER: TV above 75% of EV - DCF is mostly a terminal guess","OK"))'),
        (41, "WACC minus g", f'=IF({A["wacc"]}-C22<0.02,"RED: WACC - g below 2% - terminal swamps value","OK")'),
        (42, "Terminal ROIC vs WACC", f'=IF(C23<{A["wacc"]},"RED: terminal ROIC below WACC - growth destroys value","OK")'),
        (43, "Explicit-period FCF", '=IF(SUM(D18:H18)<0,"AMBER: cumulative explicit FCF negative","OK")'),
    ]
    for r, t, f in guards:
        d[f"B{r}"] = t
        put(d, f"C{r}", f, "calc")
    flag_text(d, "C40:C43")
    note(d, "B45", "IPO capex adds assets; reflect any revenue it enables in the Neutral/Bull growth rates, with a cite.")
    widths(d, {"A": 2, "B": 40, "C": 22, "D": 13, "E": 13, "F": 13, "G": 13, "H": 13})
    footer(d)

    # ---------------------------------------------------------------- Peers
    pe = wb.create_sheet("Peers")
    title(pe, "Peer set - ILLUSTRATIVE peers, replace with real listed comparables")
    cols = ["Company", "Include (Y/N)", "Business-model match", "Basis", "CMP (Rs)", "Shares (cr)",
            "Net debt", "Revenue", "EBITDA", "PAT", "Net worth", "Rev growth", "Mcap", "EV", "P/E",
            "EV/EBITDA", "P/B", "EBITDA margin", "ROE"]
    header(pe, 4, cols, col=2)
    peers = [("Peer A (illustrative)", "Y", "Same model", "Consolidated", 520, 5.0, 150, 1800, 290, 170, 1100, 0.15),
             ("Peer B (illustrative)", "Y", "Same model", "Consolidated", 310, 9.0, 60, 2100, 300, 160, 950, 0.12),
             ("Peer C (illustrative)", "Y", "Partial - also exports", "Consolidated", 1450, 1.5, -40, 1300, 230, 140, 800, 0.20),
             ("Peer D (illustrative)", "Y", "Same model", "Consolidated", 95, 30.0, 400, 3200, 420, 210, 1500, 0.09),
             ("Peer E (illustrative)", "N", "Manufacturer - not comparable", "Consolidated", 800, 4.0, 0, 2500, 500, 320, 2000, 0.18)]
    if facts is not None:
        peers = [tuple(p) for p in facts.get("peers", [])][:8]
    P0, P1 = 5, 12
    for i in range(P1 - P0 + 1):
        r = P0 + i
        vals = peers[i] if i < len(peers) else ("", "", "", "", None, None, None, None, None, None, None, None)
        for j, v in enumerate(vals):
            col = "BCDEFGHIJKLM"[j]
            fmt = PCT if col == "M" else CR if j >= 4 else None
            put(pe, f"{col}{r}", v, "input", fmt)
        put(pe, f"N{r}", f'=IF(F{r}="","",F{r}*G{r})', "calc", CR)
        put(pe, f"O{r}", f'=IF(N{r}="","",N{r}+H{r})', "calc", CR)
        put(pe, f"P{r}", f'=IF(AND(C{r}="Y",N(K{r})>0),N{r}/K{r},"")', "calc", X)
        put(pe, f"Q{r}", f'=IF(AND(C{r}="Y",N(J{r})>0),O{r}/J{r},"")', "calc", X)
        put(pe, f"R{r}", f'=IF(AND(C{r}="Y",N(L{r})>0),N{r}/L{r},"")', "calc", X)
        put(pe, f"S{r}", f'=IF(N(I{r})>0,J{r}/I{r},"")', "calc", PCT)
        put(pe, f"T{r}", f'=IF(N(L{r})>0,K{r}/L{r},"")', "calc", PCT)
        dropdown(pe, f"C{r}", ["Y", "N"])
    stats = {14: ("Median (included)", "MEDIAN"), 15: ("Mean (included)", "AVERAGE"), 16: ("Min", "MIN"), 17: ("Max", "MAX")}
    for r, (t, fn) in stats.items():
        put(pe, f"B{r}", t, "bold")
        for c in "PQRST":
            fmt = PCT if c in "ST" else X
            put(pe, f"{c}{r}", f'=IF(COUNT({c}{P0}:{c}{P1})=0,"",{fn}({c}{P0}:{c}{P1}))', "calc", fmt, key=(r == 14))
    # issuer at floor and cap, post-issue diluted
    header(pe, 19, cols, col=2)
    for r, lab_, px in ((20, "Issuer at floor (post-issue)", A["floor"]), (21, "Issuer at cap (post-issue)", A["cap"])):
        put(pe, f"B{r}", lab_, "bold")
        put(pe, f"C{r}", "Y", "calc")
        put(pe, f"E{r}", f"={A['basis']}", "link")
        put(pe, f"F{r}", f"={px}", "link", CR)
        put(pe, f"G{r}", f"={A['pre_sh']}+{A['esop']}+IF({A['fresh_sh_fixed']}>0,{A['fresh_sh_fixed']},{A['fresh']}/F{r})",
            "calc", CR)
        put(pe, f"H{r}", f"={A['nd0']}-{A['fresh_net']}", "calc", CR)
        put(pe, f"I{r}", f"={A['rev0']}", "link", CR)
        put(pe, f"J{r}", f"={A['ebitda0']}", "link", CR)
        put(pe, f"K{r}", f"={A['pat0']}", "link", CR)
        put(pe, f"L{r}", f"={A['nw0']}+{A['fresh_net']}", "calc", CR)
        put(pe, f"M{r}", f"={A['rev0']}/{A['rev_prev']}-1", "calc", PCT)
        put(pe, f"N{r}", f"=F{r}*G{r}", "calc", CR)
        put(pe, f"O{r}", f"=N{r}+H{r}", "calc", CR)
        put(pe, f"P{r}", f'=IF(K{r}>0,N{r}/K{r},"n.m.")', "calc", X)
        put(pe, f"Q{r}", f'=IF(J{r}>0,O{r}/J{r},"n.m.")', "calc", X)
        put(pe, f"R{r}", f'=IF(L{r}>0,N{r}/L{r},"n.m.")', "calc", X)
        put(pe, f"S{r}", f"=J{r}/I{r}", "calc", PCT)
        put(pe, f"T{r}", f"=K{r}/L{r}", "calc", PCT)
    put(pe, "B23", "Premium / (discount) to peer median at cap", "bold")
    for c in "PQR":
        put(pe, f"{c}23", f'=IFERROR({c}21/{c}14-1,"")', "calc", PCT)
    note(pe, "B25", "Peer basis must match the issuer: post-issue diluted, consolidated vs standalone consistent. "
                    "Where the RHP gives no peers, build your own and disclose the set as ours.")
    note(pe, "B26", "Also anchor to recent comparable IPO pricings on the same platform where available.")
    widths(pe, {"A": 2, "B": 30, "C": 9, "D": 26, "E": 13, **{c: 11 for c in "FGHIJKLMNOPQRST"}})
    footer(pe)

    # ------------------------------------------------------------- Relative
    rl = wb.create_sheet("Relative")
    title(rl, "Relative valuation - peer median multiples applied to the issuer")
    header(rl, 4, ["Method", "Peer median", "Issuer metric", "Implied equity (Rs cr)", "Value / share (Rs)",
                   "Weight", "Usable weight", "Weighted value"], col=2)
    meth = [
        (5, "P/E x PAT", "=Peers!P14", f"={A['pat0']}", "=IF(ISNUMBER(C5),C5*D5,\"\")", A["w_pe"]),
        (6, "EV/EBITDA x EBITDA - net debt + net proceeds", "=Peers!Q14", f"={A['ebitda0']}",
         f"=IF(ISNUMBER(C6),C6*D6-{A['nd0']}+{A['fresh_net']},\"\")", A["w_eve"]),
        (7, "P/B x post-issue net worth", "=Peers!R14", f"={A['nw0']}+{A['fresh_net']}",
         "=IF(ISNUMBER(C7),C7*D7,\"\")", A["w_pb"]),
    ]
    for r, t, med, metric, eq, w in meth:
        rl[f"B{r}"] = t
        put(rl, f"C{r}", med, "link", X)
        put(rl, f"D{r}", metric, "link", CR)
        put(rl, f"E{r}", eq, "calc", CR)
        put(rl, f"F{r}", f'=IF(ISNUMBER(E{r}),E{r}/{A["post_sh"]},"")', "calc", CR)
        put(rl, f"G{r}", f"={w}", "link", PCT)
        put(rl, f"H{r}", f"=IF(ISNUMBER(F{r}),G{r},0)", "calc", PCT)
        put(rl, f"I{r}", f"=IF(ISNUMBER(F{r}),F{r}*G{r},0)", "calc", CR)
    rows = [(9, "Weighted value per share (pre-discount)", '=IF(SUM(H5:H7)=0,"n.a.",SUM(I5:I7)/SUM(H5:H7))', CR),
            (10, "Discount to peer median", f"={A['rel_disc']}", PCT),
            (11, "Relative value per share (Rs)", '=IF(ISNUMBER(F9),F9*(1-F10),"n.a.")', CR)]
    for r, t, f, fmt in rows:
        rl[f"B{r}"] = t
        rl[f"B{r}"].font = F_BOLD
        put(rl, f"F{r}", f, "calc", fmt, key=(r == 11))
    note(rl, "B13", "Relative prices reported earnings; DCF prices cash. A large gap between them is the finding.")
    widths(rl, {"A": 2, "B": 46, "C": 13, "D": 14, "E": 18, "F": 16, "G": 10, "H": 12, "I": 14})
    footer(rl)

    # ----------------------------------------------------------- Reverse DCF
    rv = wb.create_sheet("ReverseDCF")
    title(rv, "Reverse DCF - what the price asks for, one lever at a time")
    header(rv, 4, ["Item", "At floor", "At cap", "Actual / model"], col=2)
    fsh = lambda px: f"({A['pre_sh']}+{A['esop']}+IF({A['fresh_sh_fixed']}>0,{A['fresh_sh_fixed']},{A['fresh']}/{px}))"
    W, G, R_, T = A["wacc"], A["g"], A["roic"], A["tax"]
    lines = [
        (5, "Price (Rs)", lambda c, px: f"={px}", CR),
        (6, "Market cap (Rs cr)", lambda c, px: f"={px}*{fsh(px)}", CR),
        (7, "Implied EV = mcap + net debt - net proceeds", lambda c, px: f"={c}6+{A['nd0']}-{A['fresh_net']}", CR),
        (8, "Current FCFF (Y0 actual)", lambda c, px: "=DCF!$C$18", CR),
        (9, "EV / current FCFF",
         lambda c, px: f'=IF({c}8<=0,"No multiple: FCF negative - price rests on a turn not yet begun",{c}7/{c}8)', X),
        (11, "Lever 1 - implied perpetual growth on current FCFF",
         lambda c, px: f'=IF({c}8<=0,"n.m. (FCF negative)",({c}7*{W}-{c}8)/({c}7+{c}8))', PCT),
        (12, "Lever 2 - implied WACC at terminal g",
         lambda c, px: f'=IF({c}8<=0,"n.m. (FCF negative)",{c}8*(1+{G})/{c}7+{G})', PCT),
        (13, "Lever 3 - required EBIT margin (steady state)",
         lambda c, px: f"={c}7*({W}-{G})/((1+{G})*(1-{G}/{R_}))/(1-{T})/{A['rev0']}", PCT),
        (14, "Lever 4 - required NWC % of revenue (steady state)",
         lambda c, px: f'=IF((DCF!$C$13-{A["k"]}*{A["rev0"]}*{G}-{c}7*({W}-{G})/(1+{G}))<0,'
                       f'"Unreachable: needs negative working capital",'
                       f'(DCF!$C$13-{A["k"]}*{A["rev0"]}*{G}-{c}7*({W}-{G})/(1+{G}))/({A["rev0"]}*{G}))', PCT),
    ]
    for r, t, fn, fmt in lines:
        rv[f"B{r}"] = t
        put(rv, f"C{r}", fn("C", A["floor"]), "calc", fmt)
        put(rv, f"D{r}", fn("D", A["cap"]), "calc", fmt)
    actual = {11: (f"={G}", "terminal g used"), 12: (f"={W}", "model WACC"),
              13: ("=DCF!$C$11/DCF!$C$7", "actual EBIT margin"), 14: (f"={A['nwc0']}/{A['rev0']}", "actual NWC %")}
    for r, (f, t) in actual.items():
        put(rv, f"E{r}", f, "link", PCT)
        note(rv, f"F{r}", t)
    put(rv, "B16", "In plain words (at cap)", "bold")
    put(rv, "C16", '=IF(D8<=0,"Current free cash flow is negative: no multiple can be stated, and the entire price '
                   'rests on a turn that has not yet begun.","The price asks the business to deliver "&TEXT(D9,"0.0")'
                   '&" times its current free cash flow, in perpetuity.")', "calc")
    note(rv, "B18", "Levers 1-2 use actual Y0 FCFF (Gordon). Levers 3-4 use a steady state: capex = D&A + k x dRev, "
                    "terminal reinvestment g/ROIC. One implausible lever is an argument; four is a conclusion.")
    widths(rv, {"A": 2, "B": 52, "C": 22, "D": 22, "E": 16, "F": 22})
    footer(rv)

    # ----------------------------------------------------------- Sensitivity
    se = wb.create_sheet("Sensitivity")
    title(se, "Sensitivity - value per share (Rs)")
    se["B4"] = "Grid 1: WACC (rows) vs terminal growth (columns)"
    se["B4"].font = F_BOLD
    gs = [-0.01, -0.005, 0, 0.005, 0.01]
    ws_ = [-0.02, -0.01, 0, 0.01, 0.02]
    for j, dg in enumerate(gs):
        put(se, f"{'CDEFG'[j]}5", f"={G}+{dg}", "calc", PCT)
    for i, dw in enumerate(ws_):
        r = 6 + i
        put(se, f"B{r}", f"={W}+{dw}", "calc", PCT)
        for j in range(5):
            c = "CDEFG"[j]
            w, g = f"$B{r}", f"{c}$5"
            put(se, f"{c}{r}",
                f'=IF({w}-{g}<=0,"n.m.",(NPV({w},DCF!$D$18:$H$18)+DCF!$H$13*(1+{g})*(1-{g}/{R_})/({w}-{g})/(1+{w})^5'
                f'-{A["nd0"]}+{A["proc_credit"]})/{A["post_sh"]})', "calc", CR, key=(i == 2 and j == 2))
    se["B12"] = "Grid 2: NWC % of revenue (rows) vs EBITDA margin (columns) - model WACC and g"
    se["B12"].font = F_BOLD
    dm = [-0.02, -0.01, 0, 0.01, 0.02]
    dn = [-0.06, -0.03, 0, 0.03, 0.06]
    for j, x in enumerate(dm):
        put(se, f"{'CDEFG'[j]}13", f"={A['m']}+{x}", "calc", PCT)
    tvf = f"DCF!$H$7*(1+{G})*(1-{G}/{R_})/({W}-{G})*DCF!$H$19"
    for i, x in enumerate(dn):
        r = 14 + i
        put(se, f"B{r}", f"={A['nwc']}+{x}", "calc", PCT)
        for j in range(5):
            c = "CDEFG"[j]
            m, n = f"{c}$13", f"$B{r}"
            new_dnwc = f"((DCF!$D$7*{n}-DCF!$C$16)*DCF!$D$19+{n}*SUMPRODUCT(DCF!$E$7:$H$7-DCF!$D$7:$G$7,DCF!$E$19:$H$19))"
            put(se, f"{c}{r}",
                f"=DCF!$C$37+(({m}-{A['m']})*(1-{T})*(SUMPRODUCT(DCF!$D$7:$H$7,DCF!$D$19:$H$19)+{tvf})"
                f"+SUMPRODUCT(DCF!$D$17:$H$17,DCF!$D$19:$H$19)-{new_dnwc})/{A['post_sh']}",
                "calc", CR, key=(i == 2 and j == 2))
    note(se, "B20", "Centre cells (yellow) equal the DCF value. Working capital is often the dominant lever - "
                    "if Grid 2 moves value more than Grid 1, say so in the note.")
    widths(se, {"A": 2, "B": 16, **{c: 13 for c in "CDEFG"}})
    footer(se)

    # --------------------------------------------------------------- Summary
    sm = wb.create_sheet("Summary")
    title(sm, "Valuation summary")
    put(sm, "B4", '="Scenario: "&Assumptions!$D$5&"  |  Issuer: "&' + A["name"], "link")
    header(sm, 6, ["Method", "Value / share (Rs)", "Upside vs floor", "Upside vs cap"], col=2)
    vals = [(7, "DCF", "=DCF!C37"), (8, "Relative", "=Relative!F11"),
            (9, "Blended (DCF weight " + "per Assumptions)",
             f'=IF(ISNUMBER(C8),{A["w_dcf"]}*C7+(1-{A["w_dcf"]})*C8,C7)')]
    for r, t, f in vals:
        put(sm, f"B{r}", t, "bold")
        put(sm, f"C{r}", f, "link" if r < 9 else "calc", CR, key=(r == 9))
        put(sm, f"D{r}", f'=IFERROR(C{r}/{A["floor"]}-1,"")', "calc", PCT)
        put(sm, f"E{r}", f'=IFERROR(C{r}/{A["cap"]}-1,"")', "calc", PCT)
    checks = [
        (11, "DCF vs relative divergence", '=IFERROR(C7/C8-1,"n.a.")', PCT),
        (12, "Divergence flag", '=IF(ISNUMBER(C11),IF(ABS(C11)>0.25,"AMBER: DCF and relative diverge by "&TEXT(C11,"0.0%")'
                                '&" - the divergence is the finding; name its cause","OK"),"n.a.")', None),
        (13, "Objects floor price", f"={A['obj_floor']}", CR),
        (14, "Objects floor vs blended value", '=IF(ISNUMBER(C13),IF(C13>C9,"RED: objects floor sits above blended '
                                              'fair value","OK"),"n.a.")', None),
        (15, "Terminal value share", "=DCF!C40", None),
        (16, "WACC - g", "=DCF!C41", None),
        (17, "Terminal ROIC vs WACC", "=DCF!C42", None),
        (18, "Reverse DCF (at cap)", "=ReverseDCF!C16", None),
    ]
    for r, t, f, fmt in checks:
        put(sm, f"B{r}", t, "bold")
        put(sm, f"C{r}", f, "calc", fmt)
    flag_text(sm, "C12:C17")
    put(sm, "B20", "Call (Subscribe / Avoid / Neutral)", "bold")
    put(sm, "C20", "", "input", key=True)
    dropdown(sm, "C20", ["Subscribe", "Avoid", "Neutral"])
    sm["B22"] = "Record of all three scenarios (switch Assumptions!C5, paste values here)"
    sm["B22"].font = F_BOLD
    header(sm, 23, ["", "Bear", "Neutral", "Bull"], col=2)
    for i, t in enumerate(["DCF / share", "Relative / share", "Blended / share", "Upside vs cap"]):
        sm[f"B{24 + i}"] = t
        for c in "CDE":
            put(sm, f"{c}{24 + i}", None, "input", PCT if i == 3 else CR)
    note(sm, "B29", "Upside is reported as a percentage only. No position sizing. Returns are pre-tax.")
    sm["B31"] = DISCLAIMER
    sm["B31"].font = F_BOLD
    widths(sm, {"A": 2, "B": 40, "C": 34, "D": 16, "E": 16})
    footer(sm)

    wb.move_sheet("Summary", offset=-6)
    finalize(wb)
    wb.calculation.fullCalcOnLoad = True
    wb.save(path)
    return A


if __name__ == "__main__":
    build("03_Peer_Comps_Valuation.xlsx")
