#!/usr/bin/env python3
"""Compute RFM scores and segments for P14 (SastaBazaar, SAMPLE data).

R = days since last order, measured to the snapshot date 2025-12-31.
F = number of orders in 2025. M = total spend in 2025 (PKR).

Scores are quintile scores (1-5) by rank (ntile): customers are sorted
by the metric and split into five equal groups, so each score holds
~20% of customers. Ties are broken deterministically by customer_id —
the generator shuffles archetypes before assigning ids, so id order
does not correlate with behaviour and the tie split is neutral. A
re-run with the same seed reproduces identical scores, and the SQL
NTILE version (sql/rfm_segments.sql) agrees exactly. R is scored in
reverse (most recent = 5). Because one-time buyers are 40% of the
base, F scores 1 and 2 are both mostly one-time buyers — the honest
shape of a real shop's frequency, not a forced split.

Segment map (R score, F score) — a complete partition of all 25
combinations, standard RFM practice, with Champions kept selective
(top frequency quintile only, so the label means something):
  Champions          R>=4, F=5
  Loyal Customers    R>=3, F>=3 (not Champions)
  Potential Loyalists R>=4, F=2 / R=4, F=1 / R=3, F in 1..2
  New Customers      R=5, F=1
  At Risk            R in 1..2, F>=3
  Hibernating        R in 1..2, F=2
  Lost               R in 1..2, F=1

Run: python3 src/rfm.py
Outputs: data/processed/rfm_scores.csv, outputs/segment_summary.json
"""
import csv
import json
import statistics
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "orders_SAMPLE.csv"
PROCESSED = ROOT / "data" / "processed"
OUT = ROOT / "outputs"
SNAPSHOT = date(2025, 12, 31)
SEGMENT_ORDER = ["Champions", "Loyal Customers", "Potential Loyalists",
                 "New Customers", "At Risk", "Hibernating", "Lost"]


def quintile_scores(sorted_values, reverse=False):
    """Assign 1..5 by rank position (ntile). sorted_values: list of
    (customer_id, value) sorted ascending by value, then customer_id.
    Each score holds ~20% of customers. Returns {customer_id: score}."""
    n = len(sorted_values)
    scores = {}
    for rank, (cid, _v) in enumerate(sorted_values):
        s = min(5, rank * 5 // n + 1)
        scores[cid] = (6 - s) if reverse else s
    return scores


def segment(r_score, f_score):
    if r_score >= 4 and f_score == 5:
        return "Champions"
    if r_score >= 3 and f_score >= 3:
        return "Loyal Customers"
    if r_score == 5 and f_score == 1:
        return "New Customers"
    if r_score >= 4 and f_score == 2:
        return "Potential Loyalists"
    if r_score == 4 and f_score == 1:
        return "Potential Loyalists"
    if r_score == 3 and f_score in (1, 2):
        return "Potential Loyalists"
    if r_score <= 2 and f_score >= 3:
        return "At Risk"
    if r_score <= 2 and f_score == 2:
        return "Hibernating"
    return "Lost"  # R in 1..2, F == 1


def main():
    orders = list(csv.DictReader(open(RAW, encoding="utf-8")))
    per_customer = defaultdict(list)
    for o in orders:
        per_customer[o["customer_id"]].append(o)

    customers = []
    for cid, os_ in per_customer.items():
        last = max(date.fromisoformat(o["order_date"]) for o in os_)
        first = min(date.fromisoformat(o["order_date"]) for o in os_)
        customers.append({
            "customer_id": cid,
            "customer_name": os_[0]["customer_name"],
            "customer_email": os_[0]["customer_email"],
            "city": os_[0]["city"],
            "first_order": first.isoformat(),
            "last_order": last.isoformat(),
            "recency_days": (SNAPSHOT - last).days,
            "frequency": len(os_),
            "monetary": sum(int(o["total_amount"]) for o in os_),
        })

    # Quintile scores (rank-based ntile, deterministic).
    r_sorted = sorted(((c["customer_id"], c["recency_days"]) for c in customers),
                      key=lambda t: (t[1], t[0]))
    r_score = quintile_scores(r_sorted, reverse=True)
    f_sorted = sorted(((c["customer_id"], c["frequency"]) for c in customers),
                      key=lambda t: (t[1], t[0]))
    f_score = quintile_scores(f_sorted)
    m_sorted = sorted(((c["customer_id"], c["monetary"]) for c in customers),
                      key=lambda t: (t[1], t[0]))
    m_score = quintile_scores(m_sorted)

    for c in customers:
        c["r_score"] = r_score[c["customer_id"]]
        c["f_score"] = f_score[c["customer_id"]]
        c["m_score"] = m_score[c["customer_id"]]
        c["rfm_score"] = (c["r_score"] * 100 + c["f_score"] * 10
                          + c["m_score"])
        c["segment"] = segment(c["r_score"], c["f_score"])
        c["avg_order_value"] = round(c["monetary"] / c["frequency"])

    customers.sort(key=lambda c: c["customer_id"])

    PROCESSED.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    fields = ["customer_id", "customer_name", "customer_email", "city",
              "first_order", "last_order", "recency_days", "frequency",
              "monetary", "avg_order_value", "r_score", "f_score",
              "m_score", "rfm_score", "segment"]
    with open(PROCESSED / "rfm_scores.csv", "w", newline="",
              encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(customers)

    total_revenue = sum(c["monetary"] for c in customers)
    total_orders = len(orders)
    seg_rows = []
    for seg in SEGMENT_ORDER:
        members = [c for c in customers if c["segment"] == seg]
        rev = sum(c["monetary"] for c in members)
        seg_rows.append({
            "segment": seg,
            "customers": len(members),
            "share_of_customers_pct": round(100 * len(members) / len(customers), 1),
            "orders": sum(c["frequency"] for c in members),
            "revenue_pkr": rev,
            "share_of_revenue_pct": round(100 * rev / total_revenue, 1),
            "avg_monetary_pkr": round(rev / len(members)) if members else 0,
            "avg_recency_days": round(statistics.mean(c["recency_days"] for c in members)) if members else 0,
            "avg_frequency": round(statistics.mean(c["frequency"] for c in members), 2) if members else 0,
        })

    at_risk = next(s for s in seg_rows if s["segment"] == "At Risk")
    hibernating = next(s for s in seg_rows if s["segment"] == "Hibernating")
    lost = next(s for s in seg_rows if s["segment"] == "Lost")
    champions = next(s for s in seg_rows if s["segment"] == "Champions")

    summary = {
        "shop": "SastaBazaar (SAMPLE)",
        "snapshot_date": SNAPSHOT.isoformat(),
        "period": "2025-01-01 to 2025-12-31",
        "orders": total_orders,
        "customers": len(customers),
        "total_revenue_pkr": total_revenue,
        "avg_order_value_pkr": round(total_revenue / total_orders),
        "median_monetary_pkr": int(statistics.median(c["monetary"] for c in customers)),
        "median_recency_days": int(statistics.median(c["recency_days"] for c in customers)),
        "median_frequency": int(statistics.median(c["frequency"] for c in customers)),
        "one_time_buyers": sum(1 for c in customers if c["frequency"] == 1),
        "one_time_share_pct": round(100 * sum(1 for c in customers if c["frequency"] == 1) / len(customers), 1),
        "repeat_buyers": sum(1 for c in customers if c["frequency"] >= 2),
        "champions": champions,
        "money_at_stake_pkr": at_risk["revenue_pkr"] + hibernating["revenue_pkr"] + lost["revenue_pkr"],
        "money_at_stake_customers": at_risk["customers"] + hibernating["customers"] + lost["customers"],
        "segments": seg_rows,
        "score_counts": {
            "r": dict(sorted(Counter(c["r_score"] for c in customers).items(), key=lambda kv: str(kv[0]))),
            "f": dict(sorted(Counter(c["f_score"] for c in customers).items(), key=lambda kv: str(kv[0]))),
            "m": dict(sorted(Counter(c["m_score"] for c in customers).items(), key=lambda kv: str(kv[0]))),
        },
    }
    (OUT / "segment_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")
    print(f"{len(customers)} customers, {total_orders} orders, "
          f"PKR {total_revenue:,} total")
    for s in seg_rows:
        print(f"  {s['segment']:<20} {s['customers']:>3} customers  "
              f"PKR {s['revenue_pkr']:>9,} ({s['share_of_revenue_pct']}%)")
    print(f"money at stake (At Risk + Hibernating + Lost): "
          f"PKR {summary['money_at_stake_pkr']:,}")


if __name__ == "__main__":
    main()
