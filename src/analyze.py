#!/usr/bin/env python3
"""Regenerate the findings report for P14 from the computed summary.

Every number in the report is recomputed from
outputs/segment_summary.json — nothing is typed by hand.

Run: python3 src/analyze.py   (after src/rfm.py)
Output: outputs/segment_report.md
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "outputs" / "segment_summary.json"
REPORT = ROOT / "outputs" / "segment_report.md"

ACTIONS = {
    "Champions": ("Keep them close. Early access to new stock, a loyalty "
                  "perk, and ask them to refer a friend — they are the "
                  "shop's best salespeople."),
    "Loyal Customers": ("Grow their basket. Bundles and cross-sell on the "
                        "categories they already buy; a small step turns a "
                        "Loyal customer into a Champion."),
    "Potential Loyalists": ("Get the second order. A welcome offer and an "
                           "introduction to the best-sellers, sent while "
                           "the first order is still fresh."),
    "New Customers": ("Onboard, don't sell. A thank-you and a second-order "
                      "incentive inside 30 days — most new customers are "
                      "decided in the first month."),
    "At Risk": ("Win them back now. These customers used to buy often and "
                "have gone quiet — a personal offer this month, before "
                "they become Lost."),
    "Hibernating": ("Re-activate gently. A 'we miss you' offer and a short "
                    "survey asking why they left; expect a low reply rate "
                    "and do not overspend here."),
    "Lost": ("One last try. A single win-back offer, then stop spending on "
             "them — the money is better used keeping the At Risk group."),
}


def pkr(n):
    return f"PKR {n:,}"


def main():
    s = json.loads(SUMMARY.read_text(encoding="utf-8"))
    seg = {x["segment"]: x for x in s["segments"]}
    ch = seg["Champions"]
    ar = seg["At Risk"]
    lines = []
    lines.append("# RFM Customer Segmentation Report — SastaBazaar (SAMPLE)")
    lines.append("")
    lines.append(f"**Shop (SAMPLE):** SastaBazaar, Lahore — general store · "
                 f"**Period:** {s['period']} · **Snapshot:** {s['snapshot_date']} · "
                 f"**Report:** 10 Nov 2026")
    lines.append("")
    lines.append("> ⚠️ **What this is and is not.** The orders file is a "
                 "fictional shop's demo data, generated to show the method. "
                 "No real customer, email or payment is involved. What is "
                 "real is the method: the same R/F/M scores, the same "
                 "segment map and the same workbook run on a real client's "
                 "file the same way.")
    lines.append("")
    lines.append("## Business question it answers")
    lines.append("")
    lines.append("> \"Which customers matter most — who buys, who left, "
                 "and who is worth saving?\"")
    lines.append("")
    lines.append("Every customer is scored on Recency (days since last "
                 "order), Frequency (orders in 2025) and Monetary (spend in "
                 "2025), each on a 1–5 quintile scale, then placed in one "
                 "of 7 segments. The workbook (`rfm_segmentation_SAMPLE.xlsx`) "
                 "carries the same numbers as live formulas.")
    lines.append("")
    lines.append("## Headline numbers")
    lines.append("")
    lines.append(f"- **{s['orders']:,} orders** from **{s['customers']} customers** "
                 f"in 2025, **{pkr(s['total_revenue_pkr'])}** total revenue.")
    lines.append(f"- **Average order: {pkr(s['avg_order_value_pkr'])}**; "
                 f"median customer spent {pkr(s['median_monetary_pkr'])} in the year.")
    lines.append(f"- **{s['one_time_buyers']} customers ({s['one_time_share_pct']}%) "
                 f"bought once and never came back** — the shop's biggest leak.")
    lines.append(f"- **{ch['customers']} Champions ({ch['share_of_customers_pct']}%) "
                 f"bring {pkr(ch['revenue_pkr'])} — {ch['share_of_revenue_pct']}% of all revenue.**")
    lines.append(f"- **{pkr(s['money_at_stake_pkr'])} is at stake**: the revenue "
                 f"At Risk + Hibernating + Lost customers brought in 2025 "
                 f"({s['money_at_stake_customers']} customers).")
    lines.append("")
    lines.append("## 3 key findings")
    lines.append("")
    lines.append(f"1. **A small core carries the shop.** {ch['customers']} Champions "
                 f"({ch['share_of_customers_pct']}% of customers) produce "
                 f"{ch['share_of_revenue_pct']}% of revenue, spending on average "
                 f"{pkr(ch['avg_monetary_pkr'])} each in the year — about "
                 f"{round(ch['avg_monetary_pkr'] / s['median_monetary_pkr'], 1)}× the "
                 f"median customer. *So what:* losing even 10 Champions costs "
                 f"roughly {pkr(round(ch['revenue_pkr'] * 10 / ch['customers']))} a year. "
                 f"Retention of this group is the first job, before any new-customer spend.")
    lines.append(f"2. **The At Risk group is the best money on the table.** "
                 f"{ar['customers']} customers who used to buy "
                 f"{ar['avg_frequency']}× a year have gone quiet, and they spent "
                 f"{pkr(ar['revenue_pkr'])} in 2025. *So what:* a win-back offer to "
                 f"this group has a far higher expected return than chasing new "
                 f"buyers — they already know the shop. If even one in five "
                 f"returns at their old pace, that is roughly "
                 f"{pkr(round(ar['revenue_pkr'] / 5))} a year recovered.")
    lines.append(f"3. **Four in ten customers buy once and disappear.** "
                 f"{s['one_time_buyers']} of {s['customers']} customers "
                 f"({s['one_time_share_pct']}%) placed a single order. "
                 f"*So what:* the leak is at the second order, not the first — "
                 f"a second-order incentive inside 30 days is the cheapest "
                 f"growth lever the shop has, and it is aimed at the "
                 f"{seg['Potential Loyalists']['customers']} Potential Loyalists "
                 f"and {seg['New Customers']['customers']} New Customers first.")
    lines.append("")
    lines.append("## Segments")
    lines.append("")
    lines.append("| Segment | Customers | Share | Orders | Revenue (PKR) | Share of revenue | Avg spend (PKR) | Avg recency (days) |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for x in s["segments"]:
        lines.append(f"| {x['segment']} | {x['customers']} | {x['share_of_customers_pct']}% | "
                     f"{x['orders']} | {x['revenue_pkr']:,} | {x['share_of_revenue_pct']}% | "
                     f"{x['avg_monetary_pkr']:,} | {x['avg_recency_days']} |")
    lines.append(f"| **TOTAL** | **{s['customers']}** | **100%** | **{s['orders']:,}** | "
                 f"**{s['total_revenue_pkr']:,}** | **100%** | — | — |")
    lines.append("")
    lines.append("## What to do per segment")
    lines.append("")
    for x in s["segments"]:
        lines.append(f"- **{x['segment']}** ({x['customers']} customers, "
                     f"{pkr(x['revenue_pkr'])}): {ACTIONS[x['segment']]}")
    lines.append("")
    lines.append("## How to use it on a real file")
    lines.append("")
    lines.append("1. Put the client's orders file at `data/raw/orders_SAMPLE.csv` "
                 "(same columns: order_id, order_date, customer_id, "
                 "customer_name, customer_email, product_code, product_name, "
                 "category, quantity, unit_price, total_amount, payment_method, city).")
    lines.append("2. Re-run `python3 src/rfm.py`, `python3 src/build_sqlite.py`, "
                 "`python3 src/analyze.py`, `python3 src/build_workbook.py`, "
                 "`python3 src/checks.py` — the report, the workbook and the "
                 "checks rebuild themselves from the new rows.")
    lines.append("3. The segment map and the SQL in `sql/rfm_segments.sql` stay "
                 "with the client: re-running the SQL on next quarter's orders "
                 "re-segments every customer the same way.")
    lines.append("")
    lines.append("## Limits — what this delivery does not do")
    lines.append("")
    lines.append("- **Demo data, one year.** A real client's file has its own "
                 "order mix, its own seasonality and its own customer ids — "
                 "the segment sizes here describe SastaBazaar's sample, not "
                 "any real shop.")
    lines.append("- **Quintiles are relative, not absolute.** A customer scores 5 "
                 "for being in the top 20% of *this* file. On a different file "
                 "the same behaviour can score differently — compare segments "
                 "within one run, not scores across files.")
    lines.append("- **RFM describes the past; it does not predict the future.** "
                 "At Risk customers may return on their own, and Champions may "
                 "leave. The actions are the standard playbook for each segment, "
                 "not a forecast.")
    lines.append("- **No contact data is real.** The emails in the sample are "
                 "@example.com placeholders. A real win-back campaign needs the "
                 "client's own consented contact list.")
    lines.append("")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {REPORT}")


if __name__ == "__main__":
    main()
