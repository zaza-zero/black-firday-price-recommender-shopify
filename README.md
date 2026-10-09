# Shopify Black Friday price recommender: safe price range table

Stage 1 builds a per-product safe price range from the store's weekly sales history. Any Black Friday price recommendation has to stay inside this range.

- `data/store_weekly_sales_history.csv`: the Shopify weekly sales export (input)
- `build_price_table.py`: builds the table, with one row per product (stdlib only, no installs)
- `price_table_output.txt`: the full printed table from running the script on the dataset

```
python build_price_table.py > price_table_output.txt
```

The table's columns are `product_id` (the key), `weeks_of_history`, `min_price`, `max_price`, `distinct_prices`, `single_price` and `sparse_history`. The safe range is `[min_price, max_price]`.

How the data is cleaned:
- Duplicate product-week rows are dropped.
- Weeks with zero units sold are skipped, because a price nobody paid is not evidence that it is safe.
- A product is marked sparse when it sold in fewer than 8 weeks.
