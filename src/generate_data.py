#!/usr/bin/env python3
"""Generate the SAMPLE orders file for P14 (RFM Customer Segmentation).

Fictional shop: SastaBazaar, Lahore — general store, Jan–Dec 2025.
Customers are built in archetypes (Champions, Loyal, regulars,
one-time buyers, lapsed, new) so the RFM spread is realistic: a few
Champions, many one-time buyers, some lapsed. Nothing here is real
client data — the segmentation method is the product, the file proves it.

Run: python3 src/generate_data.py
Outputs: data/raw/orders_SAMPLE.csv
"""
import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
SEED = 20261110
SNAPSHOT = date(2025, 12, 31)  # recency is measured to this date

# Product master: code -> (name, category, price PKR). Same everyday
# general-store range as the portfolio's other sample shops.
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
CITIES = ["Lahore", "Karachi", "Islamabad", "Rawalpindi", "Faisalabad", "Multan"]
PAYMENTS = ["Cash on Delivery", "Bank Transfer", "JazzCash", "Easypaisa", "Card"]
FIRST = ["Ahmed", "Fatima", "Bilal", "Ayesha", "Usman", "Zainab", "Hassan",
         "Maryam", "Ali", "Sana", "Omar", "Hira", "Danish", "Rabia", "Imran",
         "Nida", "Saad", "Mahnoor", "Tariq", "Amna", "Kashif", "Sadia",
         "Waqas", "Mehwish", "Raza", "Farah", "Shahid", "Nadia", "Asif",
         "Kiran"]
LAST = ["Khan", "Ahmed", "Malik", "Hussain", "Ali", "Raza", "Iqbal",
        "Sheikh", "Butt", "Chaudhry", "Mirza", "Siddiqui", "Qureshi",
        "Rana", "Awan", "Abbasi", "Shah", "Javed", "Akhtar", "Nawaz"]

# Archetype: (count, orders range, last-order window, basket multiplier)
# last-order window is (earliest, latest) day-offsets before SNAPSHOT.
YEAR_START = date(2025, 1, 1)
ARCHETYPES = [
    # (name, n_customers, min_orders, max_orders, last_min_days_ago, last_max_days_ago, basket_mult)
    ("champion", 20, 10, 18, 0, 20, 1.6),
    ("loyal", 70, 6, 9, 30, 180, 1.2),
    ("regular", 140, 2, 4, 0, 180, 1.0),
    ("one_time", 140, 1, 1, 0, 364, 0.9),
    ("lapsed", 70, 2, 3, 150, 364, 0.9),
    ("new", 60, 1, 1, 0, 15, 1.0),
]


def _order_dates(rng, n, last_min_ago, last_max_ago):
    """n order dates in 2025, the latest one inside the given window."""
    last_ago = rng.randint(last_min_ago, last_max_ago)
    last = SNAPSHOT - timedelta(days=last_ago)
    dates = [last]
    for _ in range(n - 1):
        # earlier orders spread back from the last one, inside the year
        back = rng.randint(7, 300)
        d = last - timedelta(days=back)
        if d < YEAR_START:
            d = YEAR_START + timedelta(days=rng.randrange(30))
        dates.append(d)
    return sorted(dates)


def main():
    rng = random.Random(SEED)
    customers = []
    for i in range(sum(a[1] for a in ARCHETYPES)):
        name = f"{rng.choice(FIRST)} {rng.choice(LAST)}"
        email = f"{name.lower().replace(' ', '.')}{i}@example.com"
        customers.append({"customer_id": f"SB-C{i + 1:04d}", "name": name,
                          "email": email, "city": rng.choice(CITIES)})

    # Archetype slots, shuffled before assignment: customer_id order
    # must not correlate with archetype, or the quintile tiebreak
    # (customer_id) would push whole archetypes into one score.
    slots = []
    for arche, n, omin, omax, lmin, lmax, mult in ARCHETYPES:
        slots += [(arche, omin, omax, lmin, lmax, mult)] * n
    rng.shuffle(slots)

    rows = []
    order_no = 0
    ci = 0
    archetype_counts = {}
    for arche, omin, omax, lmin, lmax, mult in slots:
        archetype_counts[arche] = archetype_counts.get(arche, 0) + 1
        cust = customers[ci]
        ci += 1
        n_orders = rng.randint(omin, omax)
        for d in _order_dates(rng, n_orders, lmin, lmax):
            order_no += 1
            code, pname, cat, price = rng.choice(PRODUCTS)
            qty = max(1, round(rng.randint(1, 6) * mult))
            # basket: sometimes a second line is folded into one order
            # total by scaling quantity, keeping one row per order.
            rows.append({
                "order_id": f"SB-{10001 + order_no - 1}",
                "order_date": d.isoformat(),
                "customer_id": cust["customer_id"],
                "customer_name": cust["name"],
                "customer_email": cust["email"],
                "product_code": code,
                "product_name": pname,
                "category": cat,
                "quantity": str(qty),
                "unit_price": str(price),
                "total_amount": str(qty * price),
                "payment_method": rng.choice(PAYMENTS),
                "city": cust["city"],
            })

    rng.shuffle(rows)  # file order is not chronological on purpose
    RAW.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys())
    with open(RAW / "orders_SAMPLE.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    total = sum(int(r["total_amount"]) for r in rows)
    print(f"wrote {len(rows)} orders, {len(customers)} customers, "
          f"total PKR {total:,}")
    print(f"archetypes: {archetype_counts}")
    print(f"date range: {min(r['order_date'] for r in rows)} .. "
          f"{max(r['order_date'] for r in rows)}")


if __name__ == "__main__":
    main()
