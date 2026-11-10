-- P14 — RFM logic in SQL (SastaBazaar, SAMPLE data)
-- Recomputes R/F/M and the segment for every customer straight from
-- fact_orders, independently of src/rfm.py. The two must agree exactly
-- (src/checks.py compares them customer by customer).
--
-- Snapshot date is 2025-12-31. Quintile scores are NTILE(5) over the
-- customer base: R is NTILE over recency ascending, then reversed
-- (most recent = 5); F and M are NTILE ascending. Ties inside NTILE
-- are ordered by customer_id; the generator shuffles archetypes
-- before assigning ids, so the tie split is neutral (see src/rfm.py).
--
-- Run:  sqlite3 data/processed/rfm.db < sql/rfm_segments.sql
-- Each query is labelled; the last one is the segment summary.

-- 1. Raw R/F/M per customer (the same numbers as dim_customer).
WITH rfm_raw AS (
    SELECT customer_id,
           CAST(julianday('2025-12-31') - julianday(MAX(order_date)) AS INTEGER) AS recency_days,
           COUNT(*) AS frequency,
           SUM(total_amount) AS monetary
    FROM fact_orders
    GROUP BY customer_id
),
-- 2. Quintile scores via NTILE(5).
scored AS (
    SELECT customer_id, recency_days, frequency, monetary,
           6 - NTILE(5) OVER (ORDER BY recency_days ASC, customer_id ASC) AS r_score,
           NTILE(5) OVER (ORDER BY frequency ASC, customer_id ASC) AS f_score,
           NTILE(5) OVER (ORDER BY monetary ASC, customer_id ASC) AS m_score
    FROM rfm_raw
)
-- 3. Segment per the standard map (Champions kept to the top
--    frequency quintile so the label stays selective).
SELECT customer_id, recency_days, frequency, monetary,
       r_score, f_score, m_score,
       r_score * 100 + f_score * 10 + m_score AS rfm_score,
       CASE
           WHEN r_score >= 4 AND f_score = 5 THEN 'Champions'
           WHEN r_score >= 3 AND f_score >= 3 THEN 'Loyal Customers'
           WHEN r_score = 5 AND f_score = 1 THEN 'New Customers'
           WHEN r_score >= 4 AND f_score = 2 THEN 'Potential Loyalists'
           WHEN r_score = 4 AND f_score = 1 THEN 'Potential Loyalists'
           WHEN r_score = 3 AND f_score IN (1, 2) THEN 'Potential Loyalists'
           WHEN r_score <= 2 AND f_score >= 3 THEN 'At Risk'
           WHEN r_score <= 2 AND f_score = 2 THEN 'Hibernating'
           ELSE 'Lost'
       END AS segment
FROM scored
ORDER BY customer_id;
