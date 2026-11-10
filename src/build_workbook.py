#!/usr/bin/env python3
"""Build the client deliverable workbook for P14 (SastaBazaar, SAMPLE).

Sheets:
  Dashboard   — KPIs + segment table, all LIVE formulas over the
                Customers sheet (COUNTIFS / SUMIFS / AVERAGEIFS).
                Medians are computed in Python and stored as values:
                Excel has no MEDIANIFS, and the plain AGGREGATE form
                miscalculates in LibreOffice (see 2026-11-08 lesson).
  Segments    — one row per segment: customers, orders, revenue,
                shares and averages, all live formulas.
  Customers   — all 500 customers with R/F/M, quintile scores,
                RFM score and segment (values from src/rfm.py).
  RFM Scores  — quintile score counts + the segment map, for the
                client to read how every customer was classified.

Run: python3 src/build_workbook.py   (after src/rfm.py)
Output: outputs/rfm_segmentation_SAMPLE.xlsx
"""
import csv
import json
import statistics
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[1]
SCORES = ROOT / "data" / "processed" / "rfm_scores.csv"
SUMMARY = ROOT / "outputs" / "segment_summary.json"
OUT = ROOT / "outputs" / "rfm_segmentation_SAMPLE.xlsx"

SEGMENTS = ["Champions", "Loyal Customers", "Potential Loyalists",
            "New Customers", "At Risk", "Hibernating", "Lost"]
SEGMENT_ACTIONS = {
    "Champions": "Reward & retain: early access, loyalty perks, referral ask.",
    "Loyal Customers": "Grow basket: bundles, cross-sell, upsell to Champion.",
    "Potential Loyalists": "Second-purchase nudge: welcome offer, best-seller intro.",
    "New Customers": "Onboard: thank-you + second-order incentive within 30 days.",
    "At Risk": "Win back now: personal offer before they go quiet for good.",
    "Hibernating": "Re-activate: 'we miss you' offer, survey why they left.",
    "Lost": "Last try only: one win-back, then stop spending on them.",
}

TITLE_FONT = Font(bold=True, size=14)
HEAD_FONT = Font(bold=True, size=11, color="FFFFFF")
HEAD_FILL = PatternFill("solid", fgColor="1F4E5F")
KPI_FONT = Font(bold=True, size=12)
MONEY_FMT = '#,##0'
PCT_FMT = '0.0%'


def style_header(ws, row, ncols):
    for c in range(1, ncols + 1):
        cell = ws.cell(row=row, column=c)
        cell.font = HEAD_FONT
        cell.fill = HEAD_FILL
        cell.alignment = Alignment(horizontal="center", wrap_text=True)


def main():
    scores = list(csv.DictReader(open(SCORES, encoding="utf-8")))
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    n = len(scores)
    last_row = n + 1  # Customers sheet: header row 1, data rows 2..n+1

    wb = Workbook()

    # ---------- Customers (values) ----------
    ws = wb.active
    ws.title = "Customers"
    headers = ["Customer ID", "Customer Name", "Email", "City",
               "First Order", "Last Order", "Recency (days)", "Frequency",
               "Monetary (PKR)", "Avg Order (PKR)", "R", "F", "M",
               "RFM Score", "Segment"]
    ws.append(headers)
    style_header(ws, 1, len(headers))
    for s in scores:
        ws.append([s["customer_id"], s["customer_name"], s["customer_email"],
                   s["city"], s["first_order"], s["last_order"],
                   int(s["recency_days"]), int(s["frequency"]),
                   int(s["monetary"]), int(s["avg_order_value"]),
                   int(s["r_score"]), int(s["f_score"]), int(s["m_score"]),
                   int(s["rfm_score"]), s["segment"]])
    widths = [12, 20, 30, 12, 12, 12, 14, 10, 15, 14, 5, 5, 5, 10, 20]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    for r in range(2, last_row + 1):
        ws.cell(row=r, column=9).number_format = MONEY_FMT
        ws.cell(row=r, column=10).number_format = MONEY_FMT
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:O{last_row}"
    cust = "'Customers'"

    # ---------- Segments (live formulas) ----------
    sg = wb.create_sheet("Segments")
    sg.append(["Segment", "Customers", "Share of Customers", "Orders",
               "Revenue (PKR)", "Share of Revenue", "Avg Spend / Customer (PKR)",
               "Avg Recency (days)", "Avg Frequency", "Recommended Action"])
    style_header(sg, 1, 10)
    for i, seg in enumerate(SEGMENTS, start=2):
        sg.cell(row=i, column=1, value=seg)
        sg.cell(row=i, column=2,
               value=f'=COUNTIF({cust}!$O$2:$O${last_row},A{i})')
        sg.cell(row=i, column=3, value=f'=IFERROR(B{i}/B$9,"")')
        sg.cell(row=i, column=4,
               value=f'=SUMIF({cust}!$O$2:$O${last_row},A{i},{cust}!$H$2:$H${last_row})')
        sg.cell(row=i, column=5,
               value=f'=SUMIF({cust}!$O$2:$O${last_row},A{i},{cust}!$I$2:$I${last_row})')
        sg.cell(row=i, column=6, value=f'=IFERROR(E{i}/E$9,"")')
        sg.cell(row=i, column=7, value=f'=IFERROR(E{i}/B{i},"")')
        sg.cell(row=i, column=8,
               value=f'=IFERROR(AVERAGEIF({cust}!$O$2:$O${last_row},A{i},{cust}!$G$2:$G${last_row}),"")')
        sg.cell(row=i, column=9,
               value=f'=IFERROR(AVERAGEIF({cust}!$O$2:$O${last_row},A{i},{cust}!$H$2:$H${last_row}),"")')
        sg.cell(row=i, column=10, value=SEGMENT_ACTIONS[seg])
    sg.cell(row=9, column=1, value="TOTAL").font = Font(bold=True)
    for col, letter in ((2, "B"), (4, "D"), (5, "E")):
        sg.cell(row=9, column=col,
               value=f"=SUM({letter}2:{letter}8)").font = Font(bold=True)
    sg.cell(row=9, column=3, value="=SUM(C2:C8)").font = Font(bold=True)
    sg.cell(row=9, column=6, value="=SUM(F2:F8)").font = Font(bold=True)
    for r in range(2, 10):
        for col in (3, 6):
            sg.cell(row=r, column=col).number_format = PCT_FMT
        for col in (5, 7):
            sg.cell(row=r, column=col).number_format = MONEY_FMT
        sg.cell(row=r, column=8).number_format = '0'
        sg.cell(row=r, column=9).number_format = '0.00'
    sg.column_dimensions["A"].width = 20
    sg.column_dimensions["B"].width = 11
    sg.column_dimensions["C"].width = 18
    sg.column_dimensions["D"].width = 9
    sg.column_dimensions["E"].width = 16
    sg.column_dimensions["F"].width = 16
    sg.column_dimensions["G"].width = 24
    sg.column_dimensions["H"].width = 17
    sg.column_dimensions["I"].width = 14
    sg.column_dimensions["J"].width = 58
    sg.freeze_panes = "A2"

    # ---------- Dashboard (live formulas over Customers + Segments) ----------
    db = wb.create_sheet("Dashboard", 0)
    db["A1"] = "RFM Customer Segmentation — SastaBazaar (SAMPLE)"
    db["A1"].font = TITLE_FONT
    db["A2"] = ("Fictional shop, Jan–Dec 2025 · Snapshot 31 Dec 2025 · "
                "SAMPLE data — method is real, customers are not.")
    db["A2"].font = Font(italic=True, size=10)
    db["A4"] = "KPI"
    db["B4"] = "Value"
    db["C4"] = "How it is calculated"
    style_header(db, 4, 3)
    seg = "'Segments'"
    kpis = [
        ("Total orders (2025)", f"=SUM({cust}!$H$2:$H${last_row})",
         "Sum of Frequency over all customers"),
        ("Customers", f"=COUNTA({cust}!$A$2:$A${last_row})",
         "Count of customer rows"),
        ("Total revenue (PKR)", f"=SUM({cust}!$I$2:$I${last_row})",
         "Sum of Monetary over all customers"),
        ("Avg order value (PKR)", f"=IFERROR(B7/B5,\"\")",
         "Total revenue / total orders"),
        ("One-time buyers", f'=COUNTIF({cust}!$H$2:$H${last_row},1)',
         "Customers with Frequency = 1"),
        ("Repeat buyers", f'=COUNTIF({cust}!$H$2:$H${last_row},">=2")',
         "Customers with Frequency >= 2"),
        ("Champions", f'=COUNTIF({cust}!$O$2:$O${last_row},"Champions")',
         "Segment = Champions"),
        ("Champions revenue (PKR)",
         f'=SUMIF({cust}!$O$2:$O${last_row},"Champions",{cust}!$I$2:$I${last_row})',
         "Monetary of Champions"),
        ("At-Risk revenue (PKR)",
         f'=SUMIF({cust}!$O$2:$O${last_row},"At Risk",{cust}!$I$2:$I${last_row})',
         "Monetary of At Risk"),
        ("Hibernating revenue (PKR)",
         f'=SUMIF({cust}!$O$2:$O${last_row},"Hibernating",{cust}!$I$2:$I${last_row})',
         "Monetary of Hibernating"),
        ("Lost revenue (PKR)",
         f'=SUMIF({cust}!$O$2:$O${last_row},"Lost",{cust}!$I$2:$I${last_row})',
         "Monetary of Lost"),
        ("Money at stake (PKR)", "=SUM(B13:B15)",
         "At Risk + Hibernating + Lost revenue — spend to win back"),
    ]
    row = 5
    for label, formula, how in kpis:
        db.cell(row=row, column=1, value=label)
        db.cell(row=row, column=2, value=formula).font = KPI_FONT
        db.cell(row=row, column=3, value=how)
        row += 1
    # Medians: values computed in Python (no MEDIANIFS in Excel).
    med_row = row
    db.cell(row=med_row, column=1, value="Median spend / customer (PKR)")
    db.cell(row=med_row, column=2,
           value=summary["median_monetary_pkr"]).font = KPI_FONT
    db.cell(row=med_row, column=3,
           value="Median, computed in Python (Excel has no MEDIANIFS)")
    db.cell(row=med_row + 1, column=1, value="Median recency (days)")
    db.cell(row=med_row + 1, column=2,
           value=summary["median_recency_days"]).font = KPI_FONT
    db.cell(row=med_row + 1, column=3,
           value="Median, computed in Python (Excel has no MEDIANIFS)")
    for r in (5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, med_row, med_row + 1):
        if r in (7, 12, 13, 14, 15, 16, med_row):
            db.cell(row=r, column=2).number_format = MONEY_FMT
    db.cell(row=8, column=2).number_format = MONEY_FMT

    seg_start = med_row + 3
    db.cell(row=seg_start, column=1,
           value="Segments at a glance (live from the Segments sheet)").font = Font(bold=True, size=12)
    db.cell(row=seg_start + 1, column=1, value="Segment")
    db.cell(row=seg_start + 1, column=2, value="Customers")
    db.cell(row=seg_start + 1, column=3, value="Share of Revenue")
    style_header(db, seg_start + 1, 3)
    for i, s in enumerate(summary["segments"]):
        r = seg_start + 2 + i
        db.cell(row=r, column=1, value=s["segment"])
        db.cell(row=r, column=2, value=f"={seg}!B{i + 2}")
        db.cell(row=r, column=3, value=f"={seg}!F{i + 2}").number_format = PCT_FMT
    tr = seg_start + 9
    db.cell(row=tr, column=1, value="TOTAL").font = Font(bold=True)
    db.cell(row=tr, column=2, value=f"=SUM(B{seg_start + 2}:B{seg_start + 8})").font = Font(bold=True)
    db.cell(row=tr, column=3, value=f"=SUM(C{seg_start + 2}:C{seg_start + 8})").font = Font(bold=True)
    db.cell(row=tr, column=3).number_format = PCT_FMT
    db.column_dimensions["A"].width = 32
    db.column_dimensions["B"].width = 20
    db.column_dimensions["C"].width = 52

    # ---------- RFM Scores (reference: counts + segment map) ----------
    rf = wb.create_sheet("RFM Scores")
    rf["A1"] = "How the scores work"
    rf["A1"].font = TITLE_FONT
    rf["A2"] = ("R = days since last order (to 31 Dec 2025) · F = orders in "
                "2025 · M = spend in 2025 (PKR). Scores are quintiles 1–5: "
                "each score holds ~20% of customers. R is reversed — the "
                "most recent customers score 5.")
    rf["A2"].alignment = Alignment(wrap_text=True, vertical="top")
    rf.merge_cells("A2:D2")
    rf.row_dimensions[2].height = 30
    rf["A4"] = "Score"
    rf["B4"] = "R: customers"
    rf["C4"] = "F: customers"
    rf["D4"] = "M: customers"
    style_header(rf, 4, 4)
    for i in range(1, 6):
        rf.cell(row=4 + i, column=1, value=i)
        rf.cell(row=4 + i, column=2,
               value=f'=COUNTIF({cust}!$K$2:$K${last_row},A{4 + i})')
        rf.cell(row=4 + i, column=3,
               value=f'=COUNTIF({cust}!$L$2:$L${last_row},A{4 + i})')
        rf.cell(row=4 + i, column=4,
               value=f'=COUNTIF({cust}!$M$2:$M${last_row},A{4 + i})')
    rf.cell(row=10, column=1, value="TOTAL").font = Font(bold=True)
    for col in ("B", "C", "D"):
        rf.cell(row=10, column=ord(col) - 64,
               value=f"=SUM({col}5:{col}9)").font = Font(bold=True)
    rf["A12"] = "Segment map (R score, F score)"
    rf["A12"].font = Font(bold=True, size=12)
    rf["A13"] = "Segment"
    rf["B13"] = "Rule"
    style_header(rf, 13, 2)
    rules = [
        ("Champions", "R ≥ 4 and F = 5 — buy often and recently"),
        ("Loyal Customers", "R ≥ 3 and F ≥ 3 — steady, not yet Champions"),
        ("Potential Loyalists", "R ≥ 4 and F = 2, or R = 4 and F = 1, or R = 3 and F = 1–2"),
        ("New Customers", "R = 5 and F = 1 — first order, very recent"),
        ("At Risk", "R = 1–2 and F ≥ 3 — used to buy often, gone quiet"),
        ("Hibernating", "R = 1–2 and F = 2 — bought twice, long ago"),
        ("Lost", "R = 1–2 and F = 1 — one order, long ago"),
    ]
    for i, (seg_name, rule) in enumerate(rules, start=14):
        rf.cell(row=i, column=1, value=seg_name)
        rf.cell(row=i, column=2, value=rule)
    rf.column_dimensions["A"].width = 22
    rf.column_dimensions["B"].width = 22
    rf.column_dimensions["C"].width = 22
    rf.column_dimensions["D"].width = 22
    rf.merge_cells("B13:D13")

    wb.active = wb["Dashboard"]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUT)
    print(f"wrote {OUT} ({n} customers, {len(SEGMENTS)} segments)")


if __name__ == "__main__":
    main()
