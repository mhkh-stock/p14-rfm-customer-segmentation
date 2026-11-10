#!/usr/bin/env python3
"""Load the SAMPLE orders + RFM scores into SQLite (P14).

Star-lite model: dim_customer (one row per customer, with R/F/M and
segment) + fact_orders (one row per order) + dim_product (master).
Rebuildable from the pushed scripts and CSVs — the .db is NOT uploaded.

Run: python3 src/build_sqlite.py   (after src/rfm.py)
Output: data/processed/rfm.db
"""
import csv
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "orders_SAMPLE.csv"
SCORES = ROOT / "data" / "processed" / "rfm_scores.csv"
DB = ROOT / "data" / "processed" / "rfm.db"
SCHEMA = ROOT / "sql" / "schema.sql"

# Product master (same as the generator's).
PRODUCTS = [
    ("GR-101", "Basmati Rice 5kg", "Grocery", 2850),
    ("GR-102", "Cooking Oil 5L", "Grocery", 3450),
    ("GR-103", "Sugar 5kg", "Grocery", 720),
    ("GR-104", "Flour 10kg", "Grocery", 1150),
    ("GR-105", "Tea 900g", "Grocery", 1980),
    ("GR-106", "Lentils 2kg", "Grocery", 640),
    ("GR-107", "Salt 1kg", "Grocery", 120),
    ("GR-108", "Spices Mix 500g", "Grocery", 890),
    ("EL-201", "LED Bulb 12W", "Electronics", 450),
    ("EL-202", "Extension Board", "Electronics", 1250),
    ("EL-203", "Ceiling Fan", "Electronics", 6800),
    ("EL-204", "Iron", "Electronics", 4200),
    ("EL-205", "Kettle 1.7L", "Electronics", 3600),
    ("EL-206", "Charger Cable", "Electronics", 650),
    ("EL-207", "Power Bank 10000mAh", "Electronics", 3800),
    ("HK-301", "Dinner Set 72pc", "Home & Kitchen", 12500),
    ("HK-302", "Non-stick Pan", "Home & Kitchen", 2900),
    ("HK-303", "Water Cooler 20L", "Home & Kitchen", 1750),
    ("HK-304", "Bedsheet Double", "Home & Kitchen", 2400),
    ("HK-305", "Towel Set", "Home & Kitchen", 1450),
    ("HK-306", "Storage Box", "Home & Kitchen", 980),
    ("CL-401", "Men Kurta", "Clothing", 3200),
    ("CL-402", "Lawn Suit 3pc", "Clothing", 4500),
    ("CL-403", "Kids Frock", "Clothing", 1800),
    ("CL-404", "Shawl Wool", "Clothing", 2600),
    ("CL-405", "Socks Pack 6", "Clothing", 750),
    ("ST-501", "Notebook A4", "Stationery", 320),
    ("ST-502", "Ballpoint Pack 10", "Stationery", 280),
    ("ST-503", "Geometry Box", "Stationery", 540),
    ("ST-504", "File Folder", "Stationery", 150),
    ("ST-505", "Glue Stick", "Stationery", 180),
    ("PC-601", "Shampoo 400ml", "Personal Care", 980),
    ("PC-602", "Soap Pack 4", "Personal Care", 620),
    ("PC-603", "Toothpaste 150g", "Personal Care", 450),
    ("PC-604", "Face Wash", "Personal Care", 780),
    ("PC-605", "Hand Wash 500ml", "Personal Care", 520),
    ("PC-606", "Talcum Powder", "Personal Care", 390),
    ("PC-607", "Hair Oil 200ml", "Personal Care", 560),
    ("PC-608", "Lotion 200ml", "Personal Care", 690),
    ("PC-609", "Razor Pack", "Personal Care", 850),
    ("PC-610", "Sanitizer 250ml", "Personal Care", 420),
]


def main():
    if DB.exists():
        DB.unlink()
    con = sqlite3.connect(DB)
    con.executescript(SCHEMA.read_text(encoding="utf-8"))

    scores = list(csv.DictReader(open(SCORES, encoding="utf-8")))
    con.executemany(
        """INSERT INTO dim_customer
           (customer_id, customer_name, customer_email, city,
            first_order, last_order, recency_days, frequency, monetary,
            avg_order_value, r_score, f_score, m_score, rfm_score, segment)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        [(s["customer_id"], s["customer_name"], s["customer_email"],
          s["city"], s["first_order"], s["last_order"],
          int(s["recency_days"]), int(s["frequency"]), int(s["monetary"]),
          int(s["avg_order_value"]), int(s["r_score"]), int(s["f_score"]),
          int(s["m_score"]), int(s["rfm_score"]), s["segment"])
         for s in scores])

    orders = list(csv.DictReader(open(RAW, encoding="utf-8")))
    con.executemany(
        """INSERT INTO fact_orders
           (order_id, order_date, customer_id, product_code, quantity,
            unit_price, total_amount, payment_method, city)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        [(o["order_id"], o["order_date"], o["customer_id"],
          o["product_code"], int(o["quantity"]), int(o["unit_price"]),
          int(o["total_amount"]), o["payment_method"], o["city"])
         for o in orders])

    con.executemany(
        "INSERT INTO dim_product VALUES (?,?,?,?)", PRODUCTS)
    con.commit()
    n_cust = con.execute("SELECT COUNT(*) FROM dim_customer").fetchone()[0]
    n_ord = con.execute("SELECT COUNT(*) FROM fact_orders").fetchone()[0]
    total = con.execute("SELECT SUM(total_amount) FROM fact_orders").fetchone()[0]
    con.close()
    print(f"rfm.db: {n_cust} customers, {n_ord} orders, PKR {total:,} total")


if __name__ == "__main__":
    main()
