# PACKAGE NOTE — P14: RFM Customer Segmentation Report

**Fiverr-ready gig title:** "I will segment your customers with RFM analysis and show you who to keep, win back, and stop chasing"

## What the buyer gets

A full customer segmentation, not a one-off spreadsheet: every
customer scored on Recency, Frequency and Monetary, placed in one of
7 segments (Champions, Loyal Customers, Potential Loyalists, New
Customers, At Risk, Hibernating, Lost), with a per-segment action
plan and the money at stake on every line. Delivered on this sample:
1,598 orders and 500 customers segmented, PKR 3,120,990 of revenue
identified as at stake across 200 At Risk / Hibernating / Lost
customers, 83 data-quality checks passing, and the SQL that
re-segments the next quarter's orders the same way.

## Tiers

| Tier | Price | Delivery | Includes |
|---|---|---|---|
| **Basic — $20** | $20 | 2 days | RFM segmentation of one orders file (up to 5,000 orders) → segment report (PDF-ready markdown) with the 3 key findings + customer list with segment per customer (CSV). |
| **Standard — $65** | $65 | 4 days | Everything in Basic + Excel segmentation workbook with live-formula KPIs (Dashboard + Segments + Customers + RFM Scores sheets) + per-segment action plan with the money at stake + the SQL that re-runs the segmentation. |
| **Premium — $140** | $140 | 7 days | Everything in Standard + a second file in the same run (e.g. last year vs this year — segment migration: who moved up, who slipped) + a quarterly re-segmentation setup (same scores, dated snapshots, segment-change report) + a 30-min walkthrough call on the findings and the win-back plan for the At Risk group. |

## What the buyer must provide

- The orders file (CSV or Excel, up to 5,000 orders Basic / 20,000
  Standard / 50,000 Premium) with at least: order id, order date,
  customer id, and order total. Customer name/email optional — the
  segmentation works without them.
- The date the file runs to (the snapshot date recency is measured
  from) — usually "today" or the last day of the period.
- Which customers, if any, to exclude (e.g. staff, test orders,
  wholesale accounts) — otherwise they are segmented like everyone else.

## Notes for the seller (Hashir)

- Sample built on a fictional shop's generated file (SastaBazaar,
  500 customers) — the segmentation is the proof to show a buyer.
  Never present the demo SastaBazaar file as a real client
  segmentation; the deliverable is the method, the sample proves it.
- Quintiles are relative: a score of 5 means "top 20% of this file",
  not an absolute threshold. Say this to the buyer up front — it is
  the trust line that stops a client comparing scores across two
  different files.
- Champions are kept to the top frequency quintile on purpose, so the
  label stays selective. If a buyer's file has a flatter frequency
  distribution, the segment sizes shift — that is the data talking,
  not a setting to tune by hand.
- For a real order, confirm in writing which columns are the
  customer key and the order total, and which customers to exclude —
  then the same scripts run on their file with only the file swapped.
- Quarterly re-segmentation (Premium) reuses the P4 snapshot-diff
  pattern: same RFM, dated snapshots, segment-migration report
  (who moved up a segment, who slipped to At Risk).
