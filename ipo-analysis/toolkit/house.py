"""House style and small helpers shared by every workbook builder.

Colour convention (model cells):
  blue font   = hard input
  black font  = formula
  green font  = cross-sheet link
  yellow fill = key decision cell
"""
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.formatting.rule import CellIsRule, FormulaRule
from openpyxl.worksheet.datavalidation import DataValidation

FUND = "Parshwanath Capital Ventures Fund | SEBI Registered CAT III AIF | IN/AIF3/25-26/2108"
DISCLAIMER = "[FIRM-APPROVED SEBI DISCLAIMER AND DISCLOSURE BLOCK TO BE INSERTED]"

NAVY, RED, AMBER, GREEN = "1F3864", "C00000", "BF8F00", "2E7D32"
F_INPUT = Font(name="Calibri", size=10, color="0000FF")
F_CALC = Font(name="Calibri", size=10, color="000000")
F_LINK = Font(name="Calibri", size=10, color="008000")
F_BOLD = Font(name="Calibri", size=10, bold=True)
F_HEAD = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
F_TITLE = Font(name="Calibri", size=14, bold=True, color=NAVY)
F_NOTE = Font(name="Calibri", size=9, italic=True, color="595959")
FILL_HEAD = PatternFill("solid", fgColor=NAVY)
FILL_KEY = PatternFill("solid", fgColor="FFFF00")
FILL_INPUT = PatternFill("solid", fgColor="EAF1FB")
FILL_RED = PatternFill("solid", fgColor="F8CBAD")
FILL_AMBER = PatternFill("solid", fgColor="FFE699")
FILL_GREEN = PatternFill("solid", fgColor="C6EFCE")
THIN = Side(style="thin", color="BFBFBF")
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP = Alignment(wrap_text=True, vertical="top")

CR = '#,##0.00'          # Rs crore, 2 decimals
PCT = '0.00%'
X = '0.00"x"'
INT = '#,##0'
DATE = 'dd-mmm-yyyy'


def as_date(v):
    """Accept ISO date strings from facts.json."""
    import datetime as _dt
    if isinstance(v, str) and len(v) == 10 and v[4] == "-":
        return _dt.date.fromisoformat(v)
    return v


def pick(facts, key, default, blank):
    """Sample default when facts is None; facts[key] if present; otherwise `blank`."""
    if facts is None:
        return default
    return facts.get(key, blank)


def sample_banner(facts):
    if facts is None:
        return "ALL SAMPLE NUMBERS ARE ILLUSTRATIVE AND MUST BE REPLACED."
    return "Issuer build: figures from the offer document (page cites in notes). BLANK cell = declared data gap."


def title(ws, text, sub=None):
    ws["A1"] = text
    ws["A1"].font = F_TITLE
    ws["A2"] = sub or FUND
    ws["A2"].font = F_NOTE
    ws.sheet_view.showGridLines = False


def header(ws, row, labels, col=1):
    for i, lab in enumerate(labels):
        c = ws.cell(row=row, column=col + i, value=lab)
        c.font, c.fill, c.alignment, c.border = F_HEAD, FILL_HEAD, Alignment(wrap_text=True, vertical="center"), BOX


def put(ws, ref, value, kind="calc", fmt=None, key=False):
    """Write a value/formula with the house colour for its kind."""
    c = ws[ref]
    c.value = value
    c.font = {"input": F_INPUT, "calc": F_CALC, "link": F_LINK, "bold": F_BOLD}[kind]
    if kind == "input":
        c.fill = FILL_INPUT
    if key:
        c.fill = FILL_KEY
    if fmt:
        c.number_format = fmt
    c.border = BOX
    return c


def note(ws, ref, text):
    ws[ref] = text
    ws[ref].font = F_NOTE
    ws[ref].alignment = Alignment(wrap_text=False, vertical="top")


def widths(ws, mapping):
    for col, w in mapping.items():
        ws.column_dimensions[col].width = w


def dropdown(ws, ref, options):
    dv = DataValidation(type="list", formula1='"' + ",".join(options) + '"', allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(ref)


def flag_text(ws, rng):
    """Colour cells whose text starts with RED / AMBER / OK / PASS / FAIL / WATCH."""
    first = rng.split(":")[0].replace("$", "")
    for word, fill in (("RED", FILL_RED), ("FAIL", FILL_RED), ("INCONSISTENT", FILL_RED),
                       ("DEGENERATE", FILL_RED), ("AMBER", FILL_AMBER), ("WATCH", FILL_AMBER),
                       ("OK", FILL_GREEN), ("PASS", FILL_GREEN)):
        ws.conditional_formatting.add(
            rng, FormulaRule(formula=[f'LEFT({first},{len(word)})="{word}"'], fill=fill))


def footer(ws):
    ws.oddFooter.left.text = FUND
    ws.oddFooter.right.text = "Page &P of &N"
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_margins.left = ws.page_margins.right = 0.71  # ~18 mm


class InputBlock:
    """Writes label/value/unit/note rows and remembers each value's absolute address."""

    def __init__(self, ws, start_row, label_col="B", value_col="C", facts=None, policy=()):
        """facts=None -> illustrative sample values. facts=dict -> issuer mode: inputs come from
        facts; any input not supplied is left BLANK (a declared gap), except house-policy keys,
        which keep their default."""
        self.ws, self.row, self.lc, self.vc = ws, start_row, label_col, value_col
        self.facts, self.policy = facts, set(policy)
        self.addr = {}

    def section(self, text):
        self.row += 1
        c = self.ws[f"{self.lc}{self.row}"]
        c.value, c.font = text, Font(bold=True, color=NAVY, size=11)
        self.row += 1

    def add(self, key, label, value, fmt=CR, kind="input", unit="", hint="", key_cell=False):
        if kind == "input" and self.facts is not None:
            value = self.facts.get(key, value if key in self.policy else None)
        value = as_date(value) if fmt == DATE else value
        r = self.row
        self.ws[f"{self.lc}{r}"] = label
        self.ws[f"{self.lc}{r}"].font = F_CALC
        put(self.ws, f"{self.vc}{r}", value, kind, fmt, key_cell)
        uc = chr(ord(self.vc) + 1)
        self.ws[f"{uc}{r}"] = unit
        self.ws[f"{uc}{r}"].font = F_NOTE
        if hint:
            note(self.ws, f"{chr(ord(self.vc) + 2)}{r}", hint)
        self.addr[key] = f"'{self.ws.title}'!${self.vc}${r}"
        self.row += 1
        return self.addr[key]
