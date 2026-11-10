-- P14 — RFM Customer Segmentation (SastaBazaar, SAMPLE data)
-- Star-lite schema: one customer dimension, one order fact, one
-- product dimension. The RFM scores live on dim_customer (computed by
-- src/rfm.py); sql/rfm_segments.sql recomputes them from fact_orders
-- so the logic can be checked independently.
--
-- Run:  sqlite3 data/processed/rfm.db < sql/schema.sql
-- (src/build_sqlite.py does this and loads the CSVs.)

CREATE TABLE IF NOT EXISTS dim_customer (
    customer_id     TEXT PRIMARY KEY,
    customer_name   TEXT NOT NULL,
    customer_email  TEXT NOT NULL,
    city            TEXT NOT NULL,
    first_order     TEXT NOT NULL,  -- ISO YYYY-MM-DD
    last_order      TEXT NOT NULL,  -- ISO YYYY-MM-DD
    recency_days    INTEGER NOT NULL,  -- days from last order to 2025-12-31
    frequency       INTEGER NOT NULL,  -- orders in 2025
    monetary        INTEGER NOT NULL,  -- total spend 2025 (PKR)
    avg_order_value INTEGER NOT NULL,
    r_score         INTEGER NOT NULL CHECK (r_score BETWEEN 1 AND 5),
    f_score         INTEGER NOT NULL CHECK (f_score BETWEEN 1 AND 5),
    m_score         INTEGER NOT NULL CHECK (m_score BETWEEN 1 AND 5),
    rfm_score       INTEGER NOT NULL,  -- R*100 + F*10 + M
    segment         TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_orders (
    order_id       TEXT PRIMARY KEY,
    order_date     TEXT NOT NULL,  -- ISO YYYY-MM-DD
    customer_id    TEXT NOT NULL REFERENCES dim_customer (customer_id),
    product_code   TEXT NOT NULL,
    quantity       INTEGER NOT NULL CHECK (quantity > 0),
    unit_price     INTEGER NOT NULL CHECK (unit_price > 0),
    total_amount   INTEGER NOT NULL CHECK (total_amount = quantity * unit_price),
    payment_method TEXT NOT NULL,
    city           TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_product (
    product_code TEXT PRIMARY KEY,
    product_name TEXT NOT NULL,
    category     TEXT NOT NULL,
    unit_price   INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_orders_customer ON fact_orders (customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_date ON fact_orders (order_date);
CREATE INDEX IF NOT EXISTS idx_customer_segment ON dim_customer (segment);
