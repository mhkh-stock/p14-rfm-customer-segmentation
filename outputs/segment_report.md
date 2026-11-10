# RFM Customer Segmentation Report — SastaBazaar (SAMPLE)

**Shop (SAMPLE):** SastaBazaar, Lahore — general store · **Period:** 2025-01-01 to 2025-12-31 · **Snapshot:** 2025-12-31 · **Report:** 10 Nov 2026

> ⚠️ **What this is and is not.** The orders file is a fictional shop's demo data, generated to show the method. No real customer, email or payment is involved. What is real is the method: the same R/F/M scores, the same segment map and the same workbook run on a real client's file the same way.

## Business question it answers

> "Which customers matter most — who buys, who left, and who is worth saving?"

Every customer is scored on Recency (days since last order), Frequency (orders in 2025) and Monetary (spend in 2025), each on a 1–5 quintile scale, then placed in one of 7 segments. The workbook (`rfm_segmentation_SAMPLE.xlsx`) carries the same numbers as live formulas.

## Headline numbers

- **1,598 orders** from **500 customers** in 2025, **PKR 11,633,750** total revenue.
- **Average order: PKR 7,280**; median customer spent PKR 11,455 in the year.
- **200 customers (40.0%) bought once and never came back** — the shop's biggest leak.
- **46 Champions (9.2%) bring PKR 3,930,420 — 33.8% of all revenue.**
- **PKR 3,120,990 is at stake**: the revenue At Risk + Hibernating + Lost customers brought in 2025 (200 customers).

## 3 key findings

1. **A small core carries the shop.** 46 Champions (9.2% of customers) produce 33.8% of revenue, spending on average PKR 85,444 each in the year — about 7.5× the median customer. *So what:* losing even 10 Champions costs roughly PKR 854,439 a year. Retention of this group is the first job, before any new-customer spend.
2. **The At Risk group is the best money on the table.** 120 customers who used to buy 3.41× a year have gone quiet, and they spent PKR 2,592,980 in 2025. *So what:* a win-back offer to this group has a far higher expected return than chasing new buyers — they already know the shop. If even one in five returns at their old pace, that is roughly PKR 518,596 a year recovered.
3. **Four in ten customers buy once and disappear.** 200 of 500 customers (40.0%) placed a single order. *So what:* the leak is at the second order, not the first — a second-order incentive inside 30 days is the cheapest growth lever the shop has, and it is aimed at the 89 Potential Loyalists and 31 New Customers first.

## Segments

| Segment | Customers | Share | Orders | Revenue (PKR) | Share of revenue | Avg spend (PKR) | Avg recency (days) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Champions | 46 | 9.2% | 447 | 3,930,420 | 33.8% | 85,444 | 32 |
| Loyal Customers | 134 | 26.8% | 542 | 3,752,230 | 32.3% | 28,002 | 84 |
| Potential Loyalists | 89 | 17.8% | 89 | 651,600 | 5.6% | 7,321 | 50 |
| New Customers | 31 | 6.2% | 31 | 178,510 | 1.5% | 5,758 | 7 |
| At Risk | 120 | 24.0% | 409 | 2,592,980 | 22.3% | 21,608 | 214 |
| Hibernating | 44 | 8.8% | 44 | 304,830 | 2.6% | 6,928 | 270 |
| Lost | 36 | 7.2% | 36 | 223,180 | 1.9% | 6,199 | 263 |
| **TOTAL** | **500** | **100%** | **1,598** | **11,633,750** | **100%** | — | — |

## What to do per segment

- **Champions** (46 customers, PKR 3,930,420): Keep them close. Early access to new stock, a loyalty perk, and ask them to refer a friend — they are the shop's best salespeople.
- **Loyal Customers** (134 customers, PKR 3,752,230): Grow their basket. Bundles and cross-sell on the categories they already buy; a small step turns a Loyal customer into a Champion.
- **Potential Loyalists** (89 customers, PKR 651,600): Get the second order. A welcome offer and an introduction to the best-sellers, sent while the first order is still fresh.
- **New Customers** (31 customers, PKR 178,510): Onboard, don't sell. A thank-you and a second-order incentive inside 30 days — most new customers are decided in the first month.
- **At Risk** (120 customers, PKR 2,592,980): Win them back now. These customers used to buy often and have gone quiet — a personal offer this month, before they become Lost.
- **Hibernating** (44 customers, PKR 304,830): Re-activate gently. A 'we miss you' offer and a short survey asking why they left; expect a low reply rate and do not overspend here.
- **Lost** (36 customers, PKR 223,180): One last try. A single win-back offer, then stop spending on them — the money is better used keeping the At Risk group.

## How to use it on a real file

1. Put the client's orders file at `data/raw/orders_SAMPLE.csv` (same columns: order_id, order_date, customer_id, customer_name, customer_email, product_code, product_name, category, quantity, unit_price, total_amount, payment_method, city).
2. Re-run `python3 src/rfm.py`, `python3 src/build_sqlite.py`, `python3 src/analyze.py`, `python3 src/build_workbook.py`, `python3 src/checks.py` — the report, the workbook and the checks rebuild themselves from the new rows.
3. The segment map and the SQL in `sql/rfm_segments.sql` stay with the client: re-running the SQL on next quarter's orders re-segments every customer the same way.

## Limits — what this delivery does not do

- **Demo data, one year.** A real client's file has its own order mix, its own seasonality and its own customer ids — the segment sizes here describe SastaBazaar's sample, not any real shop.
- **Quintiles are relative, not absolute.** A customer scores 5 for being in the top 20% of *this* file. On a different file the same behaviour can score differently — compare segments within one run, not scores across files.
- **RFM describes the past; it does not predict the future.** At Risk customers may return on their own, and Champions may leave. The actions are the standard playbook for each segment, not a forecast.
- **No contact data is real.** The emails in the sample are @example.com placeholders. A real win-back campaign needs the client's own consented contact list.

