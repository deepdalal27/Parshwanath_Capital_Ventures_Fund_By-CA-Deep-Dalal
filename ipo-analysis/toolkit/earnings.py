"""Earnings quality: is the reported P/E right?

Reads facts["earnings_quality"] (see FACTS_SCHEMA.md) and restates PAT for items that move reported profit away from
recurring, cash-backed earnings: costs capitalised instead of expensed, provision releases, deferred or unbooked
expenses, one-off income. Each adjustment is pre-tax by year (Rs crore, negative = reduces profit) with a reason, a
confidence level and a page cite. Only adjustments with "include": true enter the adjusted P/E; the rest are shown
as information, including items that would *raise* earnings, so the view stays two-sided.

Used by build_charts.py; verify.py recomputes the arithmetic independently.
"""

MATERIAL = 0.10     # an adjustment set that moves latest-year PAT by more than 10% is called out in the verdict


def _pe(price, pat, shares):
    if not (price and shares) or pat is None or pat <= 0:
        return None
    return price / (pat / shares)


def assess(eq, pat_hist, years, price, shares, tax_default=0.2517):
    """eq: facts["earnings_quality"]; pat_hist: reported PAT for the three years (Rs crore)."""
    if not eq or not pat_hist or pat_hist[-1] is None:
        return None
    tax = eq.get("tax", tax_default)
    adjs = []
    for a in eq.get("adjustments", []):
        pre = [(x or 0.0) for x in (a.get("pre_tax") or [0, 0, 0])][:3]
        post = [round(x * (1 - tax), 4) for x in pre]
        adjs.append({**a, "pre_tax": pre, "post_tax": post, "include": bool(a.get("include"))})

    latest, rows = pat_hist[-1], []
    rows.append({"basis": f"Reported {years[-1]}", "pat": latest})
    running = latest
    for a in adjs:
        if a["include"]:
            running += a["post_tax"][-1]
            rows.append({"basis": f"{years[-1]} after: {a.get('short') or a.get('item')}", "pat": round(running, 4)})
    adj_hist = [p + sum(a["post_tax"][i] for a in adjs if a["include"]) if p is not None else None
                for i, p in enumerate(pat_hist)]
    if all(p is not None for p in pat_hist):
        rows.append({"basis": f"{years[0]}-{years[-1]} average, reported", "pat": round(sum(pat_hist) / 3, 4)})
        rows.append({"basis": f"{years[0]}-{years[-1]} average, adjusted", "pat": round(sum(adj_hist) / 3, 4)})
    for r in rows:
        r["eps"] = round(r["pat"] / shares, 4) if shares else None
        r["pe"] = round(_pe(price, r["pat"], shares), 2) if _pe(price, r["pat"], shares) else None

    for a in adjs:          # standalone effect of each item on the latest-year P/E, included or not
        a["pe_if_applied"] = round(_pe(price, latest + a["post_tax"][-1], shares), 2) if _pe(price, latest + a["post_tax"][-1], shares) else None

    adj_latest = adj_hist[-1]
    move = (adj_latest - latest) / latest if latest else 0
    pe_rep, pe_adj = _pe(price, latest, shares), _pe(price, adj_latest, shares)
    if abs(move) <= MATERIAL:
        verdict = (f"Reported P/E is a fair measure: the adjustments found move {years[-1]} PAT by "
                   f"{move:+.1%}, within the {MATERIAL:.0%} threshold.")
    else:
        verdict = (f"Reported {years[-1]} P/E of {pe_rep:.1f}x is flattered by the items flagged: adjusted P/E "
                   f"{'n.m. (adjusted PAT not positive)' if pe_adj is None else f'{pe_adj:.1f}x'} "
                   f"(PAT {move:+.1%}).") if move < 0 else (
                   f"Reported {years[-1]} P/E of {pe_rep:.1f}x understates earnings: adjusted P/E {pe_adj:.1f}x (PAT {move:+.1%}).")
    avg = [r for r in rows if "average" in r["basis"]]
    if len(avg) == 2 and avg[0]["pe"] and avg[1]["pe"]:
        verdict += (f" On the {years[0]}-{years[-1]} average, which smooths one-year items, the P/E is "
                    f"{avg[0]['pe']:.1f}x reported and {avg[1]['pe']:.1f}x adjusted.")
    return {"years": years, "price": price, "shares": shares, "tax": tax, "rows": rows, "adjustments": adjs,
            "adjusted_pat": [round(x, 4) if x is not None else None for x in adj_hist],
            "pe_reported": round(pe_rep, 2) if pe_rep else None, "pe_adjusted": round(pe_adj, 2) if pe_adj else None,
            "pat_change": round(move, 4), "material": abs(move) > MATERIAL, "verdict": verdict,
            "flags": [a.get("reason") or a.get("item") for a in adjs if a["include"]],
            "checked": eq.get("checked", [])}
