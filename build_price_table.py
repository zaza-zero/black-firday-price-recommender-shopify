"""Build the per-product safe price range table from the Shopify weekly sales export.

One row per product (product_id is the key). For each product:
  weeks_of_history  distinct weeks the product sold at least one unit
  min_price         lowest price it actually sold at
  max_price         highest price it actually sold at
  distinct_prices   how many different prices it sold at
  single_price      True when only one price was ever seen
  sparse_history    True when weeks_of_history < MIN_WEEKS

The safe range is [min_price, max_price]: a Black Friday recommendation should
stay inside the prices this product has already sold at.

Run: python build_price_table.py [path/to/export.csv]
"""

import csv
import sys
from pathlib import Path

DEFAULT_CSV = Path(__file__).parent / "data" / "store_weekly_sales_history.csv"
MIN_WEEKS = 8  # fewer selling weeks than this = too little history to trust the range


def load_weeks(path):
    """Return {product_id: {week_start_date: price}} for weeks that sold units.

    The export repeats some product-week rows; keying by week drops the copies.
    Weeks with zero units sold are skipped: a price nobody paid is not evidence
    that the price is safe.
    """
    weeks, dupes, zero_unit = {}, 0, 0
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            if int(row["units_sold"]) == 0:
                zero_unit += 1
                continue
            product = weeks.setdefault(row["product_id"], {})
            if row["week_start_date"] in product:
                dupes += 1
                continue
            product[row["week_start_date"]] = float(row["price"])
    return weeks, dupes, zero_unit


def build_table(weeks):
    rows = []
    for product_id in sorted(weeks):
        prices = list(weeks[product_id].values())
        distinct = len(set(prices))
        rows.append({
            "product_id": product_id,
            "weeks_of_history": len(prices),
            "min_price": min(prices),
            "max_price": max(prices),
            "distinct_prices": distinct,
            "single_price": distinct == 1,
            "sparse_history": len(prices) < MIN_WEEKS,
        })
    return rows


def print_table(rows):
    headers = list(rows[0])
    cells = [[f"{v:.2f}" if isinstance(v, float) else str(v) for v in r.values()] for r in rows]
    widths = [max(len(h), *(len(c[i]) for c in cells)) for i, h in enumerate(headers)]
    print("  ".join(h.ljust(w) for h, w in zip(headers, widths)))
    print("  ".join("-" * w for w in widths))
    for c in cells:
        print("  ".join(v.ljust(w) for v, w in zip(c, widths)).rstrip())


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CSV
    weeks, dupes, zero_unit = load_weeks(path)
    rows = build_table(weeks)

    print(f"Source: {path.name}")
    print(f"Products: {len(rows)} | duplicate product-week rows dropped: {dupes} | "
          f"zero-unit weeks skipped: {zero_unit}\n")
    print_table(rows)

    sparse = [r for r in rows if r["sparse_history"]]
    print(f"\nSparse cutoff: weeks_of_history < {MIN_WEEKS} selling weeks.")
    for r in sparse:
        print(f"  {r['product_id']}: only {r['weeks_of_history']} selling weeks "
              f"(< {MIN_WEEKS}), so its range is too thin to trust on its own.")
    if not sparse:
        print("  No product fell below the cutoff.")


if __name__ == "__main__":
    main()
