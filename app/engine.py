"""Inventory maths, kept separate from the Streamlit UI so it can be tested.

Every function here takes and returns plain pandas objects. The dashboard
calls these; tests/test_engine.py checks them against hand-worked answers.
"""
import numpy as np
import pandas as pd

# How sure you want to be of not running out during a delivery wait -> z score
SERVICE_LEVELS = {"90%": 1.28, "95%": 1.65, "98%": 2.05, "99%": 2.33}

# Minimum number of full periods of history before we trust the measured
# variability. Below this we fall back to a Poisson assumption (std = sqrt(rate)).
MIN_PERIODS = {1: 14, 7: 4, 30: 4}


def detect_granularity(sales):
    """Work out whether each sales row is a day, a week or a month of sales.

    Returns (label, period_days). Daily POS exports have a sale on almost every
    calendar day across the store; summary sheets have one row per product per
    week or month.
    """
    s = sales[["Style_No", "Date_of_Sale"]].dropna().copy()
    s["Date_of_Sale"] = pd.to_datetime(s["Date_of_Sale"]).dt.normalize()
    dates = np.sort(s["Date_of_Sale"].unique())
    if len(dates) < 2:
        return "daily", 1
    global_gap = np.median(np.diff(dates) / np.timedelta64(1, "D"))
    if global_gap <= 1:
        return "daily", 1
    per_sku = (
        s.drop_duplicates()
        .sort_values(["Style_No", "Date_of_Sale"])
        .groupby("Style_No")["Date_of_Sale"]
        .diff()
        .dt.days.dropna()
    )
    if per_sku.empty:
        return "daily", 1
    med = per_sku.median()
    if med >= 20:
        return "monthly", 30
    if med >= 5:
        return "weekly", 7
    return "daily", 1


def _bucket_stats(w, as_of, window_days, period):
    """Count, mean and std of sales totals per `period`-day bucket, per product.
    Buckets run backwards from as_of; only full buckets inside each product's
    window are used, and buckets with no sales count as zero."""
    n_buckets = (window_days // period).astype(int)
    idx = window_days.index
    x = w[["Style_No", "Date_of_Sale", "Units_Sold"]].copy()
    x["Bucket"] = (as_of - x["Date_of_Sale"]).dt.days // period
    x = x.join(n_buckets.rename("N"), on="Style_No")
    x = x[x["Bucket"] < x["N"]]
    b = x.groupby(["Style_No", "Bucket"])["Units_Sold"].sum()
    b_sum = b.groupby(level=0).sum().reindex(idx).fillna(0)
    b_sq = (b ** 2).groupby(level=0).sum().reindex(idx).fillna(0)
    n = n_buckets.astype(float)
    mean_b = b_sum / n.where(n > 0)
    var_b = (b_sq - n * mean_b ** 2) / (n - 1).where(n > 1)
    return n_buckets, mean_b, np.sqrt(var_b.clip(lower=0))


def demand_stats(sales, as_of=None, lookback_days=90):
    """Daily sales rate and day-to-day variability for every product.

    - Sales are added up per product per day first (many transactions on one
      day count as one day of demand).
    - Days with no sales count as zero.
    - The window ends at the last date in the data (not each product's last
      sale), so products that stopped selling slow down instead of looking busy.
    - The window starts at the later of: `lookback_days` before the end, or the
      start of the product's first sales period. New products aren't diluted.
    - For weekly/monthly summary rows, variability is measured across periods
      and converted to a daily figure (std / sqrt(period length)).
    """
    s = sales[["Style_No", "Date_of_Sale", "Units_Sold"]].dropna(subset=["Date_of_Sale"]).copy()
    s["Date_of_Sale"] = pd.to_datetime(s["Date_of_Sale"]).dt.normalize()
    s["Units_Sold"] = pd.to_numeric(s["Units_Sold"], errors="coerce").fillna(0)
    if as_of is None:
        as_of = s["Date_of_Sale"].max()
    as_of = pd.Timestamp(as_of).normalize()
    granularity, period = detect_granularity(s)

    g = s.groupby("Style_No")["Date_of_Sale"]
    first, last = g.min(), g.max()
    window_floor = as_of - pd.Timedelta(days=lookback_days - 1)
    start = (first - pd.Timedelta(days=period - 1)).clip(lower=window_floor)
    window_days = ((as_of - start).dt.days + 1).clip(lower=1)

    s = s.join(start.rename("Start"), on="Style_No")
    w = s[(s["Date_of_Sale"] >= s["Start"]) & (s["Date_of_Sale"] <= as_of)].copy()
    total = w.groupby("Style_No")["Units_Sold"].sum().reindex(first.index).fillna(0)
    rate = (total / window_days).clip(lower=0)

    # Variability: totals per period (bucket), counting empty periods as zero.
    n_buckets, mean_b, std_b = _bucket_stats(w, as_of, window_days, period)
    enough = n_buckets >= MIN_PERIODS.get(period, 4)
    measured_std = std_b / np.sqrt(period)
    poisson_std = np.sqrt(rate)
    daily_std = measured_std.where(enough, poisson_std).fillna(poisson_std)

    # Confidence: how steady are weekly (or monthly) totals? Day-to-day
    # wobble is always high for slow sellers, so judge on weeks at least.
    conf_period = max(period, 7)
    n_c, mean_c, std_c = _bucket_stats(w, as_of, window_days, conf_period)
    cv = (std_c / mean_c).where(mean_c > 0)
    confidence = np.where(
        ~enough | (n_c < 3), "Low — little history",
        np.where(cv < 0.5, "High", np.where(cv < 1.0, "Medium", "Low")),
    )

    out = pd.DataFrame({
        "Style_No": first.index,
        "First_Sale": first.values,
        "Last_Sale": last.values,
        "Days_Since_Last_Sale": (as_of - last).dt.days.values,
        "Window_Days": window_days.values,
        "Units_In_Window": total.values,
        "Daily_Sales_Rate": rate.round(3).values,
        "Daily_Std": daily_std.round(3).values,
        "Confidence": confidence,
    })
    out.attrs["granularity"] = granularity
    out.attrs["period_days"] = period
    out.attrs["as_of"] = as_of
    return out


def plan_orders(df, cover_days=30, demand_pct=0.0, extra_lead=0, z=1.65, slow_days=60):
    """Reorder point / order-up-to plan.

    Expects columns: Daily_Sales_Rate, Daily_Std, Lead_Time, MOQ,
    Units_On_Hand, Units_On_Order.

    - Buffer stock = z * daily std * sqrt(lead time)
    - Reorder point = expected sales during the delivery wait + buffer
    - Target level  = expected sales during (delivery wait + cover period) + buffer
    - Stock position = on hand + already on order
    - Order only when stock position <= reorder point; then order
      target - stock position, rounded up to the minimum order quantity.
    - Products with no sale in the last `slow_days` days are never reordered
      automatically (one-off or discontinued items).
    """
    r = df.copy()
    rate = r["Daily_Sales_Rate"].fillna(0) * (1 + demand_pct)
    lead = r["Lead_Time"].astype(float) + extra_lead
    r["Adj_Rate"] = rate
    r["Adj_Lead"] = lead
    r["Cover_Days"] = cover_days
    r["Buffer_Stock"] = np.ceil(z * r["Daily_Std"].fillna(0) * np.sqrt(lead))
    r["Lead_Demand"] = rate * lead
    r["Cover_Demand"] = rate * cover_days
    r["Reorder_Point"] = np.ceil(r["Lead_Demand"] + r["Buffer_Stock"])
    r["Target_Level"] = np.ceil(r["Lead_Demand"] + r["Cover_Demand"] + r["Buffer_Stock"])
    r["Stock_Position"] = r["Units_On_Hand"].fillna(0) + r["Units_On_Order"].fillna(0)

    selling = rate > 0
    if "Days_Since_Last_Sale" in r:
        selling &= r["Days_Since_Last_Sale"].fillna(9999) <= slow_days
    r["Needs_Order"] = (r["Stock_Position"] <= r["Reorder_Point"]) & selling
    gap = (r["Target_Level"] - r["Stock_Position"]).clip(lower=0)
    r["Raw_Order"] = np.where(r["Needs_Order"], np.ceil(gap), 0)
    moq = r["MOQ"].fillna(0)
    r["MOQ_Applied"] = r["Needs_Order"] & (r["Raw_Order"] < moq)
    r["Units_to_Order"] = np.where(r["Needs_Order"], np.maximum(r["Raw_Order"], moq), 0).astype(int)

    # Forecast for the cover period with a range
    spread = z * r["Daily_Std"].fillna(0) * np.sqrt(cover_days)
    r["Forecast"] = np.round(r["Cover_Demand"])
    r["Forecast_Lower"] = np.round((r["Cover_Demand"] - spread).clip(lower=0))
    r["Forecast_Upper"] = np.round(r["Cover_Demand"] + spread)

    # Timing
    r["Days_On_Hand"] = np.where(rate > 0, r["Units_On_Hand"].fillna(0) / rate.where(rate > 0), np.inf)
    r["Days_Until_Reorder"] = np.where(
        rate > 0, ((r["Stock_Position"] - r["Reorder_Point"]) / rate.where(rate > 0)).clip(lower=0), np.inf
    )
    # Days you'd be empty before a new order lands (ignores on-order timing)
    r["Stockout_Gap_Days"] = np.where(
        r["Needs_Order"], np.ceil((lead - r["Stock_Position"] / rate.where(rate > 0)).clip(lower=0)), 0
    )
    r["Stockout_Gap_Days"] = r["Stockout_Gap_Days"].fillna(0)

    def prio(row):
        if not row["Needs_Order"]:
            return "Not yet"
        if row["Stockout_Gap_Days"] > 0:
            return "Urgent"
        return "Order now"

    r["Priority"] = r.apply(prio, axis=1)
    if "Cost_Price" in r:
        r["Amount_to_Spend"] = (r["Units_to_Order"] * r["Cost_Price"].fillna(0)).round(0)
    return r


def stock_status(r, slow_days=60):
    """One status per product. Expects plan_orders output plus Days_Since_Last_Sale."""
    def one(row):
        on_hand = row["Units_On_Hand"]
        rate = row["Adj_Rate"]
        since = row.get("Days_Since_Last_Sale", 0)
        if on_hand <= 0 and rate > 0:
            return "Out of Stock"
        if rate <= 0 or (pd.notna(since) and since > slow_days):
            return "Not Selling" if on_hand > 0 else "Inactive"
        if row["Stockout_Gap_Days"] > 0:
            return "Critical"
        if row["Needs_Order"]:
            return "Reorder Now"
        days_cover = row["Stock_Position"] / rate
        if days_cover > row["Adj_Lead"] + 2 * row["Cover_Days"] + 30:
            return "Overstock"
        return "Healthy"
    return r.apply(one, axis=1)


PRIORITY_RANK = {"Urgent": 0, "Order now": 1, "Not yet": 2}


def fit_budget(orders, budget):
    """Mark which orders fit in the budget, most urgent first.

    Within the same priority, products that run out soonest go first.
    """
    o = orders.copy()
    o["_rank"] = o["Priority"].map(PRIORITY_RANK).fillna(3)
    o = o.sort_values(["_rank", "Days_On_Hand"])
    o["Cumulative_Spend"] = o["Amount_to_Spend"].cumsum()
    o["In_Budget"] = o["Cumulative_Spend"] <= budget
    # once something doesn't fit, smaller later items may still fit
    spent, flags = 0.0, []
    for amt in o["Amount_to_Spend"]:
        if spent + amt <= budget:
            spent += amt
            flags.append(True)
        else:
            flags.append(False)
    o["In_Budget"] = flags
    return o.drop(columns=["_rank", "Cumulative_Spend"])
