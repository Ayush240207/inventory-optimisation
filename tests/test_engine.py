"""Known-answer tests for the inventory maths. Run with:  python -m pytest tests"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from engine import demand_stats, detect_granularity, fit_budget, plan_orders, stock_status  # noqa: E402

END = pd.Timestamp("2026-06-30")


def daily(sku, qty_by_day, end=END):
    """qty_by_day[i] is units sold i days before the last day (index 0 = oldest)."""
    n = len(qty_by_day)
    dates = pd.date_range(end - pd.Timedelta(days=n - 1), end)
    return pd.DataFrame({"Style_No": sku, "Date_of_Sale": dates, "Units_Sold": qty_by_day})


def stats_for(df, sku, **kw):
    s = demand_stats(df, **kw)
    return s.set_index("Style_No").loc[sku]


# ── Sales rate ───────────────────────────────────────────

def test_steady_daily_seller():
    df = daily("A", [4] * 90)
    st = stats_for(df, "A")
    assert st["Daily_Sales_Rate"] == pytest.approx(4)
    assert st["Daily_Std"] == pytest.approx(0)
    assert detect_granularity(df) == ("daily", 1)


def test_many_transactions_per_day_are_added_up_first():
    # 2 transactions of 2 units each day = 4/day with no day-to-day variation.
    one = daily("A", [2] * 30)
    df = pd.concat([one, one])
    st = stats_for(df, "A")
    assert st["Daily_Sales_Rate"] == pytest.approx(4)
    assert st["Daily_Std"] == pytest.approx(0)


def test_zero_days_count():
    # sells 10 units every other day -> 5/day, std of [10,0,10,0...] ≈ 5.04
    df = daily("A", [10, 0] * 30)
    df = df[df["Units_Sold"] > 0]  # POS exports leave out zero days
    filler = daily("Z", [1] * 60)   # another product makes the store "daily"
    st = stats_for(pd.concat([df, filler]), "A")
    assert st["Daily_Sales_Rate"] == pytest.approx(5, abs=0.1)
    assert st["Daily_Std"] == pytest.approx(5.04, abs=0.1)


def test_single_sale_is_not_a_fast_seller():
    # Old bug: one row of 10 units -> 10 units/day.
    filler = daily("Z", [1] * 90)
    one_off = pd.DataFrame({"Style_No": ["B"], "Date_of_Sale": [END - pd.Timedelta(days=79)], "Units_Sold": [10]})
    st = stats_for(pd.concat([filler, one_off]), "B")
    assert st["Daily_Sales_Rate"] == pytest.approx(10 / 80)


def test_product_that_stopped_selling_slows_down():
    # 3/day for 30 days, then nothing for 60 days -> 1/day over 90 days, not 3/day.
    filler = daily("Z", [1] * 90)
    dead = daily("C", [3] * 30, end=END - pd.Timedelta(days=60))
    st = stats_for(pd.concat([filler, dead]), "C")
    assert st["Daily_Sales_Rate"] == pytest.approx(1)
    assert st["Days_Since_Last_Sale"] == 60


def test_monthly_summary_rows():
    df = pd.DataFrame({
        "Style_No": ["M"] * 6,
        "Date_of_Sale": pd.to_datetime(["2026-01-15", "2026-02-15", "2026-03-15", "2026-04-15", "2026-05-15", "2026-06-15"]),
        "Units_Sold": [60] * 6,
    })
    assert detect_granularity(df) == ("monthly", 30)
    st = stats_for(df, "M", lookback_days=180)
    # 360 units over ~180 days (first row covers the 30 days before 15 Jan)
    assert st["Daily_Sales_Rate"] == pytest.approx(2, rel=0.05)
    # Old bug: std of the monthly rows was used as a *daily* std. Here months
    # are identical so daily variability should be tiny, not 0-vs-60 sized.
    assert st["Daily_Std"] < 1.5


def test_returns_reduce_demand_but_never_below_zero():
    filler = daily("Z", [1] * 30)
    r = pd.DataFrame({"Style_No": ["R", "R"], "Date_of_Sale": [END - pd.Timedelta(days=5), END], "Units_Sold": [2, -5]})
    st = stats_for(pd.concat([filler, r]), "R")
    assert st["Daily_Sales_Rate"] == 0


# ── Ordering ─────────────────────────────────────────────

def base(**kw):
    row = dict(Style_No="X", Daily_Sales_Rate=5.0, Daily_Std=1.5, Lead_Time=21, MOQ=60,
               Units_On_Hand=45, Units_On_Order=0, Cost_Price=100, Days_Since_Last_Sale=0)
    row.update(kw)
    return pd.DataFrame([row])


def test_order_covers_delivery_wait_plus_cover_period():
    r = plan_orders(base(), cover_days=30).iloc[0]
    buffer = np.ceil(1.65 * 1.5 * np.sqrt(21))           # 12
    assert r["Buffer_Stock"] == buffer
    assert r["Reorder_Point"] == 5 * 21 + buffer            # 117
    assert r["Target_Level"] == 5 * 51 + buffer             # 267
    assert r["Units_to_Order"] == 5 * 51 + buffer - 45      # 222
    assert r["Stockout_Gap_Days"] == 12                     # empty day 9, delivery day 21
    assert r["Priority"] == "Urgent"


def test_no_order_when_stock_is_healthy_even_with_moq():
    # Old bug: 500 units on hand still recommended ordering the MOQ.
    r = plan_orders(base(Units_On_Hand=500)).iloc[0]
    assert r["Units_to_Order"] == 0
    assert r["Priority"] == "Not yet"
    assert r["Days_Until_Reorder"] == pytest.approx((500 - 117) / 5)


def test_moq_rounds_up_only_when_ordering():
    r = plan_orders(base(Units_On_Hand=110, MOQ=200)).iloc[0]
    assert r["Needs_Order"]
    assert r["Raw_Order"] == 267 - 110
    assert r["Units_to_Order"] == 200
    assert r["MOQ_Applied"]


def test_stock_on_order_counts():
    # 45 on hand + 100 on order = 145 > reorder point 117 -> no new order
    r = plan_orders(base(Units_On_Order=100)).iloc[0]
    assert r["Units_to_Order"] == 0


def test_order_is_never_raised_to_reorder_point():
    # Old bug: final = max(raw, reorder point). Raw here is 267-115=152 (>MOQ).
    r = plan_orders(base(Units_On_Hand=115)).iloc[0]
    assert r["Units_to_Order"] == 152


def test_status_labels():
    df = pd.concat([
        base(Style_No="out", Units_On_Hand=0),
        base(Style_No="crit"),
        base(Style_No="ok", Units_On_Hand=200),
        base(Style_No="over", Units_On_Hand=2000),
        base(Style_No="dead", Daily_Sales_Rate=0, Daily_Std=0, Units_On_Hand=50),
        base(Style_No="stale", Units_On_Hand=50, Days_Since_Last_Sale=90),
    ])
    r = plan_orders(df)
    got = dict(zip(r["Style_No"], stock_status(r)))
    assert got == {"out": "Out of Stock", "crit": "Critical", "ok": "Healthy",
                   "over": "Overstock", "dead": "Not Selling", "stale": "Not Selling"}


def test_budget_keeps_urgent_first():
    df = pd.concat([
        base(Style_No="urgent", Units_On_Hand=10),            # gap>0
        base(Style_No="now", Units_On_Hand=50, Lead_Time=10, Daily_Std=0),
    ])
    r = plan_orders(df)
    r = r[r["Needs_Order"]]
    urgent_cost = float(r.loc[r["Style_No"] == "urgent", "Amount_to_Spend"].iloc[0])
    fitted = fit_budget(r, urgent_cost)
    assert fitted.set_index("Style_No").loc["urgent", "In_Budget"]
    assert not fitted.set_index("Style_No").loc["now", "In_Budget"]


def test_no_reorder_for_products_that_stopped_selling():
    # One-off item: last sale 80 days ago, low stock -> don't reorder (old code ordered the MOQ)
    r = plan_orders(base(Daily_Sales_Rate=0.125, Daily_Std=0.35, Units_On_Hand=5, Days_Since_Last_Sale=80)).iloc[0]
    assert r["Units_to_Order"] == 0
