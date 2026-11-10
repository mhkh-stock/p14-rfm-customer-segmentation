# P14 — RFM Customer Segmentation Report: who buys, who left, who is worth saving

**Client (SAMPLE):** SastaBazaar, Lahore — general store orders,
Jan–Dec 2025 · **Snapshot:** 31 Dec 2025 · **Status: SAMPLE delivery on DEMO data**
**Tools:** Python (stdlib RFM) · SQL (NTILE recompute) · SQLite · Excel (live formulas)
**Deliverable:** `outputs/rfm_segmentation_SAMPLE.xlsx`
(Dashboard + Segments + Customers + RFM Scores, 500 customers)

> ⚠️ **What this is and is not.** The orders file is a fictional
> shop's demo data, generated to show the method. No real customer,
> email or payment is involved. What is real is the method: the same
> R/F/M scores, the same segment map, the same SQL and the same
> workbook run on a real client's file the same way, and every number
> in the report is recomputed from the data, never typed.

## Business question it answers

> "Which customers matter most — who buys, who left, and who is worth saving?"

A shop that treats all customers the same spends its marketing money
in the wrong places: discounts for Champions who would buy anyway,
silence for the At Risk group that is quietly leaving. This delivery
scores every customer on Recency, Frequency and Monetary, puts each
one in a segment, and says what to do with each segment — with the
money at stake on every line.

## What is inside

| File | What it does |
|---|---|
| `outputs/rfm_segmentation_SAMPLE.xlsx` | The deliverable: Dashboard (12 live-formula KPIs + segment glance) + Segments (7 rows, all live formulas) + Customers (500 rows with R/F/M, scores, segment) + RFM Scores (quintile counts + segment map) |
| `outputs/segment_report.md` | Findings report: headline numbers, 3 key findings with "so what", segment table, per-segment actions |
| `outputs/segment_summary.json` | Machine-readable summary (KPIs + per-segment numbers + score counts) |
| `data/raw/orders_SAMPLE.csv` | The orders file: 1,598 orders, 500 customers, PKR 11,633,750 |
| `data/processed/rfm_scores.csv` | One row per customer: R/F/M, quintile scores, RFM score, segment |
| `data/processed/rfm.db` | SQLite: dim_customer + fact_orders + dim_product (NOT uploaded — rebuildable) |
| `data/README.md` | Data dictionary + known quirks |
| `sql/schema.sql` | Star-lite schema for the three tables |
| `sql/rfm_segments.sql` | The RFM logic in SQL (NTILE quintiles + segment map) — recomputes every score from the orders |
| `src/generate_data.py` | Makes the demo file (seeded; NOT run on a real client file) |
| `src/rfm.py` | Computes R/F/M, quintile scores and segments |
| `src/build_sqlite.py` | Loads orders + scores + product master into SQLite |
| `src/analyze.py` | Regenerates the report — every number recomputed, never typed |
| `src/build_workbook.py` | Builds the workbook: 4 sheets, live formulas |
| `src/checks.py` | Data-quality + reconciliation checks as code — 83 checks, all passing |
| `requirements.txt` | Pinned: `openpyxl==3.1.2` (Python 3.12; the RFM itself is stdlib-only) |

## How it fits together

```
client's orders file ──▶ src/rfm.py ──▶ data/processed/rfm_scores.csv + outputs/segment_summary.json
        (1,598 rows)            │                    │
                                ▼                    ▼
                        src/build_sqlite.py ──▶ data/processed/rfm.db
                                │              (NOT uploaded: rebuildable)
                                ▼
                        src/analyze.py ──▶ outputs/segment_report.md
                                │
                                ▼
                        src/build_workbook.py ──▶ outputs/rfm_segmentation_SAMPLE.xlsx
                                ▲ src/checks.py verifies all of it (83 checks)
```

## How the segmentation works

- **R** = days since last order, to 31 Dec 2025. **F** = orders in
  2025. **M** = spend in 2025 (PKR).
- **Scores 1–5** are quintiles (ntile): each score holds ~20% of
  customers. R is reversed — the most recent customers score 5.
  Ties are split by customer_id; the generator shuffles archetypes
  before assigning ids, so the split is neutral.
- **Segment map** (complete partition of all 25 R×F combinations):
  Champions R≥4, F=5 (top frequency quintile only, so the label stays
  selective) · Loyal Customers R≥3, F≥3 · Potential Loyalists R≥4,
  F=2 / R=4, F=1 / R=3, F=1–2 · New Customers R=5, F=1 · At Risk
  R=1–2, F≥3 · Hibernating R=1–2, F=2 · Lost R=1–2, F=1.

## 3 key findings (from this file)

1. **A small core carries the shop.** 46 Champions (9.2% of
   customers) produce 33.8% of revenue, spending on average
   PKR 85,444 each in the year — about 7.5× the median customer.
   *So what:* losing even 10 Champions costs roughly PKR 854,439 a
   year. Retention of this group is the first job, before any
   new-customer spend.
2. **The At Risk group is the best money on the table.** 120
   customers who used to buy 3.41× a year have gone quiet, and they
   spent PKR 2,592,980 in 2025. *So what:* a win-back offer to this
   group has a far higher expected return than chasing new buyers —
   they already know the shop. If even one in five returns at their
   old pace, that is roughly PKR 518,596 a year recovered.
3. **Four in ten customers buy once and disappear.** 200 of 500
   customers (40.0%) placed a single order. *So what:* the leak is at
   the second order, not the first — a second-order incentive inside
   30 days is the cheapest growth lever the shop has, and it is aimed
   at the 89 Potential Loyalists and 31 New Customers first.

## Verified numbers

| KPI | Value |
|---|---|
| Orders / customers (2025) | 1,598 / 500 |
| Total revenue / avg order value (PKR) | 11,633,750 / 7,280 |
| Median spend / customer (PKR) | 11,455 |
| One-time buyers / repeat buyers | 200 (40.0%) / 300 |
| Champions | 46 customers, PKR 3,930,420 (33.8%) |
| Loyal Customers | 134 customers, PKR 3,752,230 (32.3%) |
| Potential Loyalists | 89 customers, PKR 651,600 (5.6%) |
| New Customers | 31 customers, PKR 178,510 (1.5%) |
| At Risk | 120 customers, PKR 2,592,980 (22.3%) |
| Hibernating | 44 customers, PKR 304,830 (2.6%) |
| Lost | 36 customers, PKR 223,180 (1.9%) |
| Money at stake (At Risk + Hibernating + Lost) | PKR 3,120,990 (200 customers) |
| SQL recompute vs Python | 500/500 customers identical |
| Checks | 83 passing (`python3 src/checks.py`) |

Verification: `python3 src/checks.py` (83 checks pass — file shape,
money reconciliation to the rupee, score ranges, the segment map
re-derived for every customer, segment counts/revenue/orders summing
to the totals, the SQL recompute agreeing with Python on all 500
customers, SQLite integrity, workbook structure and formulas, and
every headline number in the report) **and** the workbook was opened
in LibreOffice, which calculated every formula: Dashboard shows 1,598
orders, 500 customers, PKR 11,633,750 total, 46 Champions,
PKR 3,120,990 money at stake, and the Segments table totals 500
customers and PKR 11,633,750 with shares summing to 100% — identical
to the Python recompute.

## Limits — what this delivery does not do

- **Demo data, one year.** A real client's file has its own order
  mix, its own seasonality and its own customer ids — the segment
  sizes here describe SastaBazaar's sample, not any real shop.
- **Quintiles are relative, not absolute.** A customer scores 5 for
  being in the top 20% of *this* file. On a different file the same
  behaviour can score differently — compare segments within one run,
  not scores across files.
- **RFM describes the past; it does not predict the future.** At Risk
  customers may return on their own, and Champions may leave. The
  actions are the standard playbook for each segment, not a forecast.
- **No contact data is real.** The emails in the sample are
  @example.com placeholders. A real win-back campaign needs the
  client's own consented contact list.
- **Open it in Excel or Google Sheets to see the numbers.** The
  workbook carries live formulas (openpyxl writes formulas, not cached
  values), so they calculate when the file is opened — a raw file
  reader that does not calculate formulas will show blanks instead of
  KPI values.

## How to run it (under 5 steps)

First time only: `pip install -r requirements.txt` (only openpyxl;
the RFM itself is Python stdlib).

1. `python3 src/generate_data.py` — makes the demo file (skip this on
   a real client file; put theirs at `data/raw/orders_SAMPLE.csv`).
2. `python3 src/rfm.py` — computes R/F/M + segments → scores + summary.
3. `python3 src/build_sqlite.py` — loads everything into SQLite.
4. `python3 src/analyze.py` — regenerates the report.
5. `python3 src/build_workbook.py` — rebuilds the workbook.
6. `python3 src/checks.py` — 83 checks, all must pass.
7. Open `outputs/rfm_segmentation_SAMPLE.xlsx` — that is the deliverable.
8. To reuse it for a real client: put their file in place of the demo
   one and re-run steps 2–6 — the report, the workbook and the checks
   rebuild themselves from the new rows, and the SQL in
   `sql/rfm_segments.sql` stays with the client for next quarter's
   re-segmentation.

## Tools

- Python 3.12 (stdlib RFM; openpyxl 3.1.2 for the workbook)
- SQLite (star-lite schema) · Excel / Google Sheets (the client's tool)

## Data source note

**SAMPLE data, generated 10 Nov 2026 for this segmentation** (seeded
Python generator, fictional shop "SastaBazaar"). No real customer,
email or payment is involved. The segmentation, the SQL, the workbook
and the report are the product; the numbers exist to prove them.

## Repo standard note

This paid project follows the portfolio repo standard (Master Plan
§3.2): README + data dictionary (`data/README.md`) + the deliverable
workbook + reproducible scripts + a Fiverr-ready package note
(`PACKAGE-NOTE.md`). The workbook is the deliverable a buyer opens;
the scripts are the proof it was built, not typed.
