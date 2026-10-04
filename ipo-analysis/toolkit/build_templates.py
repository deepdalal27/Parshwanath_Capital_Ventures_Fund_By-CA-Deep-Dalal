"""Rebuild the three blank (illustrative) templates into ipo-analysis/templates/."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_anchor      # noqa: E402
import build_screening   # noqa: E402
import build_valuation   # noqa: E402

out = os.path.join(os.path.dirname(HERE), "templates")
os.makedirs(out, exist_ok=True)
build_screening.build(os.path.join(out, "01_DRHP_Screening_Checklist.xlsx"))
build_anchor.build(os.path.join(out, "02_Anchor_QIB_Economics.xlsx"))
build_valuation.build(os.path.join(out, "03_Peer_Comps_Valuation.xlsx"))
print("templates rebuilt in", out)
