#!/usr/bin/env python3
"""Data-quality + reconciliation checks as code for P14.

Verifies: file shape, money reconciliation, RFM score ranges, the
segment map re-derived from (R, F), segment counts/revenue/orders
summing to the totals, SQL-vs-Python agreement, SQLite integrity, the
workbook structure and formulas, the report's headline numbers, and —
when outputs/.recalc/rfm_segmentation_SAMPLE.xlsx exists (built by
the LibreOffice recalc step) — that every live-formula KPI in the
workbook calculates to exactly the Python number.

Run: python3 src/checks.py        (after the full pipeline + recalc)
All checks must pass. A failure prints FAILED and exits non-zero.
"""
import csv
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "orders_SAMPLE.csv"
SCORES = ROOT / "data" / "processed" / "rfm_scores.csv"
DB = ROOT / "data" / "processed" / "rfm.db"
SUMMARY = ROOT / "outputs" / "segment_summary.json"
REPORT = ROOT / "outputs" / "segment_report.md"
WORKBOOK = ROOT / "outputs" / "rfm_segmentation_SAMPLE.xlsx"
RECALC = ROOT / "outputs" / ".recalc" / "rfm_segmentation_SAMPLE.xlsx"
SQL = ROOT / "sql" / "rfm_segments.sql"

SEGMENTS = ["Champions", "Loyal Customers", "Potential Loyalists",
            "New Customers", "At Risk", "Hibernating", "Lost"]

passed = failed = 0
failures = []


def check(name, ok, detail=""):
    global passed, failed
    if ok:
        passed += 1
    else:
        failed += 1
        failures.append(f"{name}: {detail}")
        print(f"  FAILED: {name} — {detail}")


def segment(r, f):
    if r >= 4 and f == 5:
        return "Champions"
    if r >= 3 and f >= 3:
        return "Loyal Customers"
    if r == 5 and f == 1:
        return "New Customers"
    if r >= 4 and f == 2:
        return "Potential Loyalists"
    if r == 4 and f == 1:
        return "Potential Loyalists"
    if r == 3 and f in (1, 2):
        return "Potential Loyalists"
    if r <= 2 and f >= 3:
        return "At Risk"
    if r <= 2 and f == 2:
        return "Hibernating"
    return "Lost"


def main():
    orders = list(csv.DictReader(open(RAW, encoding="utf-8")))
    scores = list(csv.DictReader(open(SCORES, encoding="utf-8")))
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    report = REPORT.read_text(encoding="utf-8")
    total_revenue = sum(int(o["total_amount"]) for o in orders)

    # --- file shape ---
    check("raw rows = 1598", len(orders) == 1598, f"got {len(orders)}")
    check("raw columns exact",
          list(orders[0].keys()) == ["order_id", "order_date", "customer_id",
              "customer_name", "customer_email", "product_code",
              "product_name", "category", "quantity", "unit_price",
              "total_amount", "payment_method", "city"])
    check("no null ids", all(o["order_id"] and o["customer_id"] for o in orders))
    check("all dates inside 2025",
          all("2025-01-01" <= o["order_date"] <= "2025-12-31" for o in orders))
    check("unique order ids", len({o["order_id"] for o in orders}) == len(orders))
    check("customers = 500", len(scores) == 500, f"got {len(scores)}")

    # --- money ---
    check("total_amount = qty x price on every row",
          all(int(o["total_amount"]) == int(o["quantity"]) * int(o["unit_price"])
              for o in orders))
    check("raw revenue = summary total",
          total_revenue == summary["total_revenue_pkr"],
          f"{total_revenue} vs {summary['total_revenue_pkr']}")
    check("scores revenue = raw revenue",
          sum(int(s["monetary"]) for s in scores) == total_revenue)
    check("orders count = summary orders",
          len(orders) == summary["orders"])

    # --- RFM values ---
    check("scores in 1..5",
          all(1 <= int(s[k]) <= 5 for s in scores for k in ("r_score", "f_score", "m_score")))
    check("recency 0..364",
          all(0 <= int(s["recency_days"]) <= 364 for s in scores))
    check("frequency >= 1", all(int(s["frequency"]) >= 1 for s in scores))
    check("monetary > 0", all(int(s["monetary"]) > 0 for s in scores))
    check("rfm_score = R*100 + F*10 + M",
          all(int(s["rfm_score"]) == int(s["r_score"]) * 100
              + int(s["f_score"]) * 10 + int(s["m_score"]) for s in scores))
    check("no null score/segment fields",
          all(all(s[k] not in ("", None) for k in
                  ("r_score", "f_score", "m_score", "segment")) for s in scores))
    for col in ("r_score", "f_score", "m_score"):
        counts = Counter(int(s[col]) for s in scores)
        check(f"{col} quintiles are 100 each",
              all(counts[i] == 100 for i in range(1, 6)), f"{dict(counts)}")

    # --- segments ---
    check("segment map re-derivation matches every customer",
          all(segment(int(s["r_score"]), int(s["f_score"])) == s["segment"]
              for s in scores))
    seg_counts = Counter(s["segment"] for s in scores)
    check("segment counts sum to 500", sum(seg_counts.values()) == 500)
    check("all 7 segments non-empty",
          all(seg_counts[s] > 0 for s in SEGMENTS), f"{dict(seg_counts)}")
    seg_rev = {s: sum(int(x["monetary"]) for x in scores if x["segment"] == s)
               for s in SEGMENTS}
    check("segment revenue sums to total",
          sum(seg_rev.values()) == total_revenue)
    seg_ord = {s: sum(int(x["frequency"]) for x in scores if x["segment"] == s)
               for s in SEGMENTS}
    check("segment orders sum to 1598", sum(seg_ord.values()) == len(orders))
    for x in summary["segments"]:
        check(f"summary segment {x['segment']} count matches",
              seg_counts[x["segment"]] == x["customers"],
              f"{seg_counts[x['segment']]} vs {x['customers']}")
        check(f"summary segment {x['segment']} revenue matches",
              seg_rev[x["segment"]] == x["revenue_pkr"])
    check("one-time buyers = 200",
          sum(1 for s in scores if int(s["frequency"]) == 1) == summary["one_time_buyers"])
    check("money at stake = At Risk + Hibernating + Lost",
          summary["money_at_stake_pkr"] == (seg_rev["At Risk"]
              + seg_rev["Hibernating"] + seg_rev["Lost"]))

    # --- SQL vs Python ---
    con = sqlite3.connect(DB)
    sql_rows = con.execute(SQL.read_text(encoding="utf-8")).fetchall()
    py = {s["customer_id"]: s for s in scores}
    mism = 0
    for cid, rec, freq, mon, r, f, m, rfm, seg in sql_rows:
        p = py[cid]
        if not (int(p["recency_days"]) == rec and int(p["frequency"]) == freq
                and int(p["monetary"]) == mon and int(p["r_score"]) == r
                and int(p["f_score"]) == f and int(p["m_score"]) == m
                and int(p["rfm_score"]) == rfm and p["segment"] == seg):
            mism += 1
    check("SQL recompute matches Python on all 500 customers", mism == 0,
          f"{mism} mismatches")

    # --- SQLite integrity ---
    check("SQLite customers = 500",
          con.execute("SELECT COUNT(*) FROM dim_customer").fetchone()[0] == 500)
    check("SQLite orders = 1598",
          con.execute("SELECT COUNT(*) FROM fact_orders").fetchone()[0] == 1598)
    check("SQLite revenue = total",
          con.execute("SELECT SUM(total_amount) FROM fact_orders").fetchone()[0]
          == total_revenue)
    check("SQLite no orphan orders",
          con.execute("SELECT COUNT(*) FROM fact_orders o LEFT JOIN "
                      "dim_customer c ON o.customer_id = c.customer_id "
                      "WHERE c.customer_id IS NULL").fetchone()[0] == 0)
    db_seg = dict(con.execute(
        "SELECT segment, COUNT(*) FROM dim_customer GROUP BY segment").fetchall())
    check("SQLite segment counts match summary",
          all(db_seg[s] == seg_counts[s] for s in SEGMENTS))
    con.close()

    # --- workbook structure + formulas ---
    wb = load_workbook(WORKBOOK)
    check("workbook sheets",
          wb.sheetnames == ["Dashboard", "Customers", "Segments", "RFM Scores"],
          f"{wb.sheetnames}")
    cust = wb["Customers"]
    check("Customers sheet rows = 500", cust.max_row == 501,
          f"max_row {cust.max_row}")
    db_ws = wb["Dashboard"]
    formulas = [db_ws.cell(row=r, column=2).value for r in range(5, 17)]
    check("Dashboard KPIs are formulas",
          all(isinstance(v, str) and v.startswith("=") for v in formulas),
          f"{formulas}")
    sg = wb["Segments"]
    seg_formulas = [sg.cell(row=r, column=c).value
                    for r in range(2, 9) for c in (2, 4, 5, 7, 8, 9)]
    check("Segments table cells are formulas",
          all(isinstance(v, str) and v.startswith("=") for v in seg_formulas))
    rf = wb["RFM Scores"]
    rf_formulas = [rf.cell(row=r, column=c).value
                   for r in range(5, 10) for c in (2, 3, 4)]
    check("RFM Scores counts are formulas",
          all(isinstance(v, str) and v.startswith("=") for v in rf_formulas))

    # --- report numbers ---
    check("report states total revenue",
          f"{summary['total_revenue_pkr']:,}" in report)
    check("report states order count", f"{summary['orders']:,}" in report)
    check("report states customer count", str(summary["customers"]) in report)
    check("report states money at stake",
          f"{summary['money_at_stake_pkr']:,}" in report)
    check("report names all 7 segments",
          all(s in report for s in SEGMENTS))

    # --- LibreOffice recalculated values (if the recalc copy exists) ---
    if RECALC.exists():
        wb2 = load_workbook(RECALC, data_only=True)
        d2 = wb2["Dashboard"]
        expected = {
            "B5": summary["orders"], "B6": summary["customers"],
            "B7": summary["total_revenue_pkr"],
            "B8": summary["avg_order_value_pkr"],
            "B9": summary["one_time_buyers"],
            "B10": summary["repeat_buyers"],
            "B11": summary["champions"]["customers"],
            "B12": summary["champions"]["revenue_pkr"],
            "B16": summary["money_at_stake_pkr"],
            "B17": summary["median_monetary_pkr"],
            "B18": summary["median_recency_days"],
        }
        for cell, want in expected.items():
            got = d2[cell].value
            check(f"recalc Dashboard {cell} = {want}",
                  got is not None and round(float(got)) == want,
                  f"got {got!r}")
        s2 = wb2["Segments"]
        for i, x in enumerate(summary["segments"], start=2):
            check(f"recalc Segments {x['segment']} customers",
                  s2.cell(row=i, column=2).value == x["customers"],
                  f"got {s2.cell(row=i, column=2).value!r}")
            check(f"recalc Segments {x['segment']} revenue",
                  s2.cell(row=i, column=5).value == x["revenue_pkr"],
                  f"got {s2.cell(row=i, column=5).value!r}")
        check("recalc Segments TOTAL revenue",
              s2.cell(row=9, column=5).value == summary["total_revenue_pkr"])
        check("recalc Segments TOTAL customers",
              s2.cell(row=9, column=2).value == summary["customers"])
    else:
        print("  NOTE: no LibreOffice recalc copy found at "
              f"{RECALC} — recalc checks skipped")

    print(f"\n{passed} passed, {failed} failed")
    if failed:
        print("Failures:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
