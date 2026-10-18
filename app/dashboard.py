import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

st.set_page_config(
    page_title="Retail Inventory Optimiser",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Global styles ─────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

* { font-family: 'Inter', sans-serif !important; }
/* Keep Streamlit's icon font, otherwise icon names show up as text
   (e.g. "keyboard_double_arrow_right") */
[data-testid="stIconMaterial"], .material-symbols-rounded, [class*="material-symbols"] {
    font-family: 'Material Symbols Rounded' !important;
}

.stApp { background-color: #0A0A0A; }
.main { background-color: #0A0A0A; }

/* Hero section */
.hero {
    background: linear-gradient(135deg, #0A0A0A 0%, #1a1a2e 50%, #0A0A0A 100%);
    padding: 80px 40px;
    text-align: center;
    border-bottom: 1px solid #222;
}
.hero-title {
    font-size: 64px;
    font-weight: 900;
    color: #FFFFFF;
    line-height: 1.1;
    margin-bottom: 20px;
}
.hero-title span {
    background: linear-gradient(90deg, #4361EE, #10B981);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.hero-subtitle {
    font-size: 20px;
    color: #AAAAAA;
    max-width: 600px;
    margin: 0 auto 40px auto;
    line-height: 1.6;
}

/* Feature cards */
.feature-card {
    background: #141414;
    border: 1px solid #222;
    border-radius: 16px;
    padding: 32px 24px;
    text-align: center;
    transition: all 0.3s;
    cursor: pointer;
    height: 100%;
    min-height: 300px;
}
.feature-card:hover {
    border-color: #4361EE;
    transform: translateY(-4px);
}
.feature-icon { font-size: 48px; margin-bottom: 16px; }
.feature-title { font-size: 20px; font-weight: 700; color: #FFFFFF; margin-bottom: 12px; }
.feature-desc { font-size: 14px; color: #AAAAAA; line-height: 1.6; }

/* Step cards */
.step-card {
    background: #141414;
    border: 1px solid #222;
    border-radius: 12px;
    padding: 24px;
    text-align: center;
}
.step-number {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: linear-gradient(135deg, #4361EE, #10B981);
    color: white;
    font-weight: 700;
    font-size: 18px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 16px auto;
}
.step-title { font-size: 16px; font-weight: 600; color: #FFFFFF; margin-bottom: 8px; }
.step-desc { font-size: 13px; color: #AAAAAA; }

/* Metric cards */
.metric-card {
    background: #141414;
    border: 1px solid #222;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
}
.metric-card {
    min-height: 136px;
    display: flex; flex-direction: column; justify-content: center;
}
.metric-value {
    font-size: clamp(16px, 2vw, 28px); font-weight: 700; margin: 8px 0;
    line-height: 1.2; word-break: keep-all; overflow-wrap: normal;
}
.metric-label {
    font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 1px;
    word-break: normal; overflow-wrap: normal; hyphens: none; line-height: 1.4;
}

/* Section titles */
.section-title {
    font-size: 28px;
    font-weight: 700;
    color: #FFFFFF;
    margin-bottom: 8px;
}
.section-subtitle {
    font-size: 15px;
    color: #AAAAAA;
    margin-bottom: 32px;
}

/* Tab styling */
.stTabs [data-baseweb="tab-list"] { gap: 8px; background: transparent; }
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    padding: 10px 24px;
    font-weight: 600;
    color: #AAAAAA;
    background: #141414;
    border: 1px solid #222;
}
.stTabs [aria-selected="true"] {
    background: #4361EE !important;
    color: #FFFFFF !important;
    border-color: #4361EE !important;
}

/* Sidebar */
.css-1d391kg { background: #0F0F0F; }
section[data-testid="stSidebar"] { background: #0F0F0F; border-right: 1px solid #222; }
section[data-testid="stSidebar"] * { color: #FFFFFF !important; }

/* Buttons */
.stButton button {
    background: linear-gradient(135deg, #4361EE, #3a0ca3);
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    padding: 12px 24px;
}

/* Dividers */
hr { border-color: #222 !important; }

/* All text white */
p, span, label, div { color: #FFFFFF; }
.stMarkdown p { color: #FFFFFF; }
h1, h2, h3, h4, h5, h6 { color: #FFFFFF !important; }

div[data-testid="metric-container"] {
    background: #141414;
    border: 1px solid #222;
    border-radius: 12px;
    padding: 15px;
}
div[data-testid="metric-container"] label { color: #AAAAAA !important; }
div[data-testid="metric-container"] [data-testid="stMetricValue"] { color: #FFFFFF !important; }

.stDataFrame { border-radius: 8px; }
.stSelectbox label { color: #FFFFFF !important; }
.stNumberInput label { color: #FFFFFF !important; }
.stFileUploader label { color: #FFFFFF !important; }
</style>
""", unsafe_allow_html=True)

def color_metric(value, label, color):
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value" style="color:{color}">{value}</div>
    </div>
    """, unsafe_allow_html=True)

def fmt_rs(v):
    """Rs 1.48 Cr / Rs 4.98 L / Rs 20,760 — keeps big totals readable in cards."""
    v = float(v)
    if abs(v) >= 1e7:
        return f"Rs {v/1e7:.2f} Cr"
    if abs(v) >= 1e5:
        return f"Rs {v/1e5:.2f} L"
    return f"Rs {v:,.0f}"

def to_excel_download(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

from loader import load_data
from engine import demand_stats, plan_orders, stock_status, fit_budget, SERVICE_LEVELS

def status_emoji(status):
    return STATUS_EMOJI.get(status, status)

STATUS_EMOJI = {"Out of Stock":"🔴 Out of Stock","Critical":"🟠 Critical","Reorder Now":"🟡 Reorder Now",
                "Healthy":"🟢 Healthy","Overstock":"🔵 Overstock","Not Selling":"⚪ Not Selling","Inactive":"⚫ Inactive"}

def priority_emoji(priority):
    return {"Urgent":"🔴 Urgent","Order now":"🟡 Order now","Not yet":"🟢 Not yet"}.get(priority, priority)

# ── Sidebar ───────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🛍️ Retail Inventory Optimiser")
    st.divider()
    st.markdown("### 📁 Upload Your Data")
    uploaded_file = st.file_uploader("Upload your data file", type=["xlsx","xls","csv"], label_visibility="collapsed")
    st.divider()
    st.markdown("### ⚙️ Store Settings")
    default_lead_time = st.number_input("Default delivery time (days)", min_value=1, max_value=90, value=21,
        help="Used only for products where your file doesn't give a lead time.")
    default_moq = st.number_input("Default minimum order quantity", min_value=1, max_value=500, value=60,
        help="Used only for products where your file doesn't give an MOQ.")
    st.caption("These fill gaps in your file. Values in your file always win.")
    st.divider()
    st.markdown("### 📥 New here?")
    template_path = "data/raw/retailer_template.xlsx"
    try:
        with open(template_path, "rb") as f:
            st.download_button("⬇️ Download Excel Template", data=f.read(), file_name="retailer_template.xlsx", use_container_width=True)
    except:
        st.info("Template not found")
    st.caption("Fill in the template with your store data and upload above")

# ── Landing page ──────────────────────────────────────
if uploaded_file is None:

    # Hero section
    st.markdown("""
    <div class="hero">
        <div class="hero-title">
            Stop Guessing.<br>
            <span>Start Knowing.</span>
        </div>
        <div class="hero-subtitle">
            The smart inventory tool for retail stores. Know exactly what to buy, 
            how much, and when — backed by data, not gut feel.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # What do you want to know section
    st.markdown("""
    <div style="text-align:center; padding: 20px 0">
        <div class="section-title">What do you want to know about your store?</div>
        <div class="section-subtitle">Upload your data and instantly get answers to the questions that matter most</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📊</div>
            <div class="feature-title">How is my store performing?</div>
            <div class="feature-desc">
                See your top 50 products by revenue and sell through rate. 
                Identify your winners to reorder and losers to cut. 
                Understand where your margins are strongest.
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📦</div>
            <div class="feature-title">What is my stock situation right now?</div>
            <div class="feature-desc">
                See exactly how many days of stock you have left for every product. 
                Know which items are critical before they run out. 
                Track what is overstocked and tying up your cash.
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🛒</div>
            <div class="feature-title">What should I order next?</div>
            <div class="feature-desc">
                Get exact order quantities for every product. 
                See the total cost before you commit. 
                Simulate different scenarios — what if demand goes up 20%?
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.divider()

    # Live scenario simulator
    st.markdown("""
    <div style="text-align:center; padding: 20px 0">
        <div class="section-title">🔧 Try a scenario — right now</div>
        <div class="section-subtitle">See how the tool thinks before you even upload your data</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        demo_velocity = st.selectbox("Daily sales rate (units/day)", [1, 2, 5, 10, 20, 50], index=2)
    with col2:
        demo_stock = st.number_input("Current stock on hand", min_value=0, value=45, step=5)
    with col3:
        demo_lead = st.selectbox("Supplier lead time (days)", [7, 14, 21, 30, 45], index=2)

    # Same maths as the real dashboard. With no history to measure, we assume
    # day-to-day sales vary by about 30% of the average.
    demo = plan_orders(pd.DataFrame([{
        "Style_No": "demo", "Daily_Sales_Rate": demo_velocity, "Daily_Std": demo_velocity * 0.3,
        "Lead_Time": demo_lead, "MOQ": 60, "Units_On_Hand": demo_stock, "Units_On_Order": 0,
        "Cost_Price": 0, "Days_Since_Last_Sale": 0,
    }]), cover_days=30).iloc[0]
    demo_status = stock_status(pd.DataFrame([demo])).iloc[0]
    demo_days_left = int(demo["Days_On_Hand"])
    demo_order = int(demo["Units_to_Order"])
    gap = int(demo["Stockout_Gap_Days"])

    if demo_status in ("Out of Stock", "Critical"):
        demo_headline, demo_color = "🔴 Critical — Order Today", "#EF4444"
        demo_detail = (f"You'll run out in {demo_days_left} days but delivery takes {demo_lead}, "
                       f"so expect about {gap} days with nothing to sell unless you can get stock sooner.")
    elif demo_status == "Reorder Now":
        demo_headline, demo_color = "🟡 Reorder Now", "#F59E0B"
        demo_detail = f"Stock is at or below the reorder point of {int(demo['Reorder_Point'])} units. Order now and it should arrive before you run out."
    elif demo_status == "Overstock":
        demo_headline, demo_color = "🔵 Overstocked", "#60A5FA"
        demo_detail = f"You have about {demo_days_left} days of stock. No order needed — this is cash sitting on the shelf."
    else:
        demo_headline, demo_color = "🟢 Healthy", "#10B981"
        demo_detail = f"No order needed yet. Reorder in about {int(demo['Days_Until_Reorder'])} days, when stock hits {int(demo['Reorder_Point'])} units."

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        color_metric(f"{demo_days_left} days", "Stock Will Last", demo_color)
    with col2:
        color_metric(f"{int(demo['Reorder_Point'])} units", "Reorder When Stock Hits", "#4361EE")
    with col3:
        color_metric(f"{int(demo['Buffer_Stock'])} units", "Buffer Stock Needed", "#F59E0B")
    with col4:
        color_metric(f"{int(demo['Forecast'])} units", "Forecast Next 30 Days", "#AAAAAA")
    with col5:
        color_metric(f"{demo_order} units" if demo_order else "None yet", "Recommended Order", "#10B981")

    st.markdown(f"""
    <div style="background:#141414; border:1px solid #222; border-left:5px solid {demo_color}; 
    border-radius:12px; padding:20px; margin-top:16px; text-align:center">
        <div style="font-size:20px; font-weight:700; color:{demo_color}">{demo_headline}</div>
        <div style="color:#DDDDDD; margin-top:8px; font-size:15px">{demo_detail}</div>
        <div style="color:#888888; margin-top:8px; font-size:13px">
            At {demo_velocity} units/day with {demo_stock} units on hand and a {demo_lead}-day lead time.
            Orders are sized to cover the delivery wait plus 30 days, with a minimum order of 60.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.divider()

    # How it works
    st.markdown("""
    <div style="text-align:center; padding: 20px 0">
        <div class="section-title">How it works</div>
        <div class="section-subtitle">Three steps to smarter buying decisions</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="step-card">
            <div class="step-number">1</div>
            <div class="step-title">Upload Your Data</div>
            <div class="step-desc">Download our Excel template, fill in your products and sales history, and upload it using the sidebar.</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="step-card">
            <div class="step-number">2</div>
            <div class="step-title">Get Instant Analysis</div>
            <div class="step-desc">The tool analyses your sales velocity, stock levels, and demand patterns across your entire catalogue.</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="step-card">
            <div class="step-number">3</div>
            <div class="step-title">Make Better Decisions</div>
            <div class="step-desc">See exactly what to order, how much, and when. Simulate scenarios and plan your buying with confidence.</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.divider()

    # Upload CTA
    st.markdown("""
    <div style="text-align:center; padding:40px 20px; background:#141414; border-radius:16px; border:1px solid #222; margin-top:20px">
        <div style="font-size:32px; font-weight:800; color:#FFFFFF; margin-bottom:12px">
            Ready to take control of your inventory?
        </div>
        <div style="color:#AAAAAA; font-size:16px; margin-bottom:24px">
            Upload your store data from the sidebar to get started
        </div>
        <div style="font-size:48px">👈</div>
        <div style="color:#4361EE; font-weight:600; font-size:16px; margin-top:8px">
            Upload your Excel file from the sidebar
        </div>
    </div>
    """, unsafe_allow_html=True)

else:
    try:
        products, sales, inventory = load_data(uploaded_file)
        sales = sales.merge(
            products[["Style_No","Product_Name","Category","Color","Gender","Cost_Price","MRP","Lead_Time_Days","MOQ"]],
            on="Style_No", how="left"
        )
        sales["Lead_Time_Days"] = sales["Lead_Time_Days"].fillna(default_lead_time)
        sales["MOQ"] = sales["MOQ"].fillna(default_moq)
        sales["Margin_Pct"] = ((sales["Selling_Price"] - sales["Cost_Price"]) / sales["Selling_Price"] * 100).round(1)
        sales["Revenue"] = sales["Units_Sold"] * sales["Selling_Price"]
        sales["Profit"] = sales["Units_Sold"] * (sales["Selling_Price"] - sales["Cost_Price"])
        today = sales["Date_of_Sale"].max()          # end of the sales data
        real_today = pd.Timestamp.today().normalize()
        has_bought = not (sales["Units_Bought"] == sales["Units_Sold"]).all()

        # ── Demand per product (shared by all tabs) ──
        stats = demand_stats(sales, as_of=today, lookback_days=90)
        granularity = stats.attrs["granularity"]

        # Every product we know about: product sheet, stock sheet or sales
        all_skus = pd.Index(products["Style_No"]).union(inventory["Style_No"]).union(sales["Style_No"]).unique()
        base = pd.DataFrame({"Style_No": all_skus}).merge(
            products[["Style_No","Product_Name","Category","Color","Gender","Cost_Price","Lead_Time_Days","MOQ"]],
            on="Style_No", how="left")
        base["Product_Name"] = base["Product_Name"].fillna(base["Style_No"])
        base["Category"] = base["Category"].fillna("Uncategorised")
        base["Color"] = base["Color"].fillna("")
        base["Gender"] = base["Gender"].fillna("")
        base["Cost_Price"] = base["Cost_Price"].fillna(0)
        base["Lead_Time"] = base["Lead_Time_Days"].fillna(default_lead_time)
        base["MOQ"] = base["MOQ"].fillna(default_moq)
        base = base.merge(stats, on="Style_No", how="left")
        for c in ["Daily_Sales_Rate","Daily_Std","Units_In_Window"]:
            base[c] = base[c].fillna(0)
        base["Days_Since_Last_Sale"] = base["Days_Since_Last_Sale"].fillna(9999)
        base["Confidence"] = base["Confidence"].fillna("Low — no sales")
        base = base.merge(inventory[["Style_No","Units_On_Hand","Units_On_Order","Expected_Delivery_Date"]], on="Style_No", how="left")
        base["Units_On_Hand"] = base["Units_On_Hand"].fillna(0)
        base["Units_On_Order"] = base["Units_On_Order"].fillna(0)
        base["Delivery_Overdue"] = (base["Units_On_Order"] > 0) & (base["Expected_Delivery_Date"] < real_today)

        st.markdown("<h1 style='color:#FFFFFF; font-size:36px; font-weight:800'>🛍️ Your Store Dashboard</h1>", unsafe_allow_html=True)
        st.caption(f"📂 {len(base)} products · {len(sales):,} sales records · Last sale: {today.strftime('%d %b %Y')} · Sales data looks {granularity}")

        stale_days = (real_today - today).days
        if stale_days > 30:
            st.warning(f"⏰ Your latest sale is from {today.strftime('%d %b %Y')}, {stale_days} days ago. "
                       "Sales rates come from that data and stock levels are treated as current — "
                       "upload fresh sales and stock figures for reliable order advice.")
        if granularity != "daily":
            st.info(f"📅 Your sales rows look like {granularity} totals rather than daily sales, so daily rates are "
                    f"averaged over each {'week' if granularity == 'weekly' else 'month'}. Daily sales data gives sharper advice.")
        n_late = int(base["Delivery_Overdue"].sum())
        if n_late:
            st.warning(f"🚚 {n_late} incoming deliveries are past their expected date. Check with your suppliers — "
                       "they're still counted as 'on order' below.")

        tab1, tab2, tab3 = st.tabs(["📊  Performance", "📦  Inventory Status", "🛒  What to Order"])

        # ── TAB 1 ─────────────────────────────────────
        with tab1:
            st.markdown("<h3 style='color:#FFFFFF'>📊 How Is Your Store Doing?</h3>", unsafe_allow_html=True)

            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                period = st.selectbox("Time Period", ["Last 30 days","Last 90 days","Last 180 days","Last 365 days","All time"], index=1)
            with col2:
                win_sellthru = st.selectbox("Winner: Min Sold %", [50,60,70,80,90], index=2, disabled=not has_bought)
            with col3:
                win_margin = st.selectbox("Winner: Min Margin %", [20,30,40,50,60], index=2)
            with col4:
                loser_sellthru = st.selectbox("Loser: Max Sold %", [20,30,40,50], index=2, disabled=not has_bought)
            with col5:
                sort_by = st.selectbox("Sort By", ["Units Sold","Revenue","Profit","Sold %","Margin %"])

            if not has_bought:
                st.info("ℹ️ Your file has no 'units bought' column, so sold % and lost-sales estimates aren't available. "
                        "Winners are your top quarter by profit (with margin above the minimum); losers are your bottom quarter by units sold.")

            sort_map = {"Units Sold":"Units_Sold","Revenue":"Revenue","Profit":"Profit","Sold %":"Sell_Through","Margin %":"Avg_Margin"}
            span_days = (today - sales["Date_of_Sale"].min()).days + 1
            days_map = {"Last 30 days":30,"Last 90 days":90,"Last 180 days":180,"Last 365 days":365,"All time":span_days}
            days = min(days_map[period], span_days)
            cutoff = today - timedelta(days=days - 1)
            period_sales = sales[sales["Date_of_Sale"] >= cutoff].copy()

            perf = period_sales.groupby("Style_No").agg(
                Product_Name=("Product_Name","first"), Category=("Category","first"),
                Color=("Color","first"), Gender=("Gender","first"),
                Units_Bought=("Units_Bought","sum"), Units_Sold=("Units_Sold","sum"),
                Revenue=("Revenue","sum"), Profit=("Profit","sum"),
                Avg_Selling_Price=("Selling_Price","mean"),
                MRP=("MRP","first"),
            ).reset_index()

            perf["Sell_Through"] = (perf["Units_Sold"] / perf["Units_Bought"].where(perf["Units_Bought"] > 0) * 100).round(1)
            if not has_bought:
                perf["Sell_Through"] = np.nan
            # revenue-weighted margin, so a few cheap clearance sales don't skew it
            perf["Avg_Margin"] = (perf["Profit"] / perf["Revenue"].where(perf["Revenue"] != 0) * 100).round(1)
            perf["Discount_Taken"] = ((perf["MRP"] - perf["Avg_Selling_Price"]) / perf["MRP"] * 100).round(1)

            # Without units bought, judge products against each other instead:
            # top quarter by profit = winners, bottom quarter by units = losers.
            if len(perf):
                profit_hi = perf["Profit"].quantile(0.75)
                units_hi = perf["Units_Sold"].quantile(0.75)
                units_lo = perf["Units_Sold"].quantile(0.25)

            def classify(row):
                if not has_bought:
                    if row["Profit"] >= profit_hi and row["Avg_Margin"] >= win_margin:
                        return "🏆 Winner"
                    if row["Units_Sold"] >= units_hi and row["Avg_Margin"] < win_margin:
                        return "📈 High Vol Low Margin"
                    if row["Units_Sold"] <= units_lo:
                        return "❌ Loser"
                    return "➡️ Average"
                if row["Sell_Through"] >= win_sellthru and row["Avg_Margin"] >= win_margin:
                    return "🏆 Winner"
                elif row["Sell_Through"] >= win_sellthru and row["Avg_Margin"] < win_margin:
                    return "📈 High Vol Low Margin"
                elif row["Sell_Through"] < loser_sellthru:
                    return "❌ Loser"
                else:
                    return "➡️ Average"

            perf["Tag"] = perf.apply(classify, axis=1) if len(perf) else []

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                color_metric(fmt_rs(perf['Revenue'].sum()), "Total Revenue", "#4361EE")
            with col2:
                color_metric(fmt_rs(perf['Profit'].sum()), "Total Profit", "#10B981")
            with col3:
                color_metric(f"{perf['Sell_Through'].mean():.1f}%" if has_bought else "—", "Avg Sold %", "#F59E0B")
            with col4:
                overall_margin = perf["Profit"].sum() / perf["Revenue"].sum() * 100 if perf["Revenue"].sum() else 0
                color_metric(f"{overall_margin:.1f}%", "Overall Margin", "#EF4444")

            st.divider()

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                color_metric(int((perf["Tag"]=="🏆 Winner").sum()), "Winners", "#10B981")
            with col2:
                color_metric(int((perf["Tag"]=="❌ Loser").sum()), "Losers", "#EF4444")
            with col3:
                color_metric(int((perf["Tag"]=="📈 High Vol Low Margin").sum()), "High Vol Low Margin", "#F59E0B")
            with col4:
                color_metric(int((perf["Tag"]=="➡️ Average").sum()), "Average", "#AAAAAA")

            st.divider()

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                cat_options = ["All"] + sorted(perf["Category"].dropna().astype(str).unique().tolist())
                cat_filter = st.selectbox("Category", cat_options, key="cat1")
            with col2:
                gender_options = ["All"] + sorted(perf["Gender"].dropna().astype(str).unique().tolist())
                gender_filter = st.selectbox("Gender", gender_options, key="gender1")
            with col3:
                tag_options = ["All","🏆 Winner","📈 High Vol Low Margin","➡️ Average","❌ Loser"]
                tag_filter = st.selectbox("Product Tag", tag_options, key="tag1")
            with col4:
                color_options = ["All"] + sorted(perf["Color"].dropna().astype(str).unique().tolist())
                color_filter = st.selectbox("Colour", color_options, key="colour1")

            filtered_perf = perf.copy()
            if cat_filter != "All":
                filtered_perf = filtered_perf[filtered_perf["Category"].astype(str) == cat_filter]
            if gender_filter != "All":
                filtered_perf = filtered_perf[filtered_perf["Gender"].astype(str) == gender_filter]
            if tag_filter != "All":
                filtered_perf = filtered_perf[filtered_perf["Tag"] == tag_filter]
            if color_filter != "All":
                filtered_perf = filtered_perf[filtered_perf["Color"].astype(str) == color_filter]

            sort_col = sort_map.get(sort_by, "Units_Sold")
            top50 = filtered_perf.sort_values(sort_col, ascending=False, na_position="last").head(50)

            top50_display = top50.rename(columns={
                "Style_No":"Style No","Product_Name":"Product",
                "Units_Sold":"Units Sold","Sell_Through":"Sold %",
                "Avg_Margin":"Margin %","Discount_Taken":"Discount %","Tag":"Tag"
            })

            st.markdown(f"<p style='color:#FFFFFF; font-weight:600'>Top {min(50, len(top50))} Products · {period.lower()}</p>", unsafe_allow_html=True)
            perf_cols = ["Style No","Product","Tag","Units Sold","Sold %","Margin %","Revenue","Profit","Discount %","Category","Color","Gender"]
            if not has_bought:
                perf_cols.remove("Sold %")
            st.dataframe(
                top50_display[perf_cols].reset_index(drop=True),
                use_container_width=True, hide_index=True,
                column_config={
                    "Sold %": st.column_config.NumberColumn(format="%.1f%%"),
                    "Margin %": st.column_config.NumberColumn(format="%.1f%%"),
                    "Discount %": st.column_config.NumberColumn(format="%.1f%%"),
                    "Revenue": st.column_config.NumberColumn("Revenue (Rs)", format="Rs %d"),
                    "Profit": st.column_config.NumberColumn("Profit (Rs)", format="Rs %d"),
                }
            )
            st.download_button("📥 Download Report", data=to_excel_download(top50), file_name="performance_report.xlsx")

            st.divider()
            st.markdown("<h3 style='color:#FFFFFF'>🔍 Estimated Lost Sales — Were You Leaving Money on the Table?</h3>", unsafe_allow_html=True)
            st.caption("Products that sold 90% or more of what you bought in this period probably ran out before it ended")

            if not has_bought:
                st.info("Needs a 'units bought' column to estimate lost sales.")
            else:
                lost_sales = perf.merge(stats[["Style_No","Daily_Sales_Rate"]], on="Style_No", how="left")
                lost_sales["Daily_Sales_Rate"] = lost_sales["Daily_Sales_Rate"].fillna(0)
                lost_sales["Stockout_Proxy"] = lost_sales["Sell_Through"] >= 90
                lost_sales["Est_Stockout_Days"] = np.where(
                    lost_sales["Stockout_Proxy"],
                    ((lost_sales["Sell_Through"] - 90) / 10 * days).clip(upper=days*0.3).round(0), 0
                )
                lost_sales["Est_Lost_Sales"] = (lost_sales["Est_Stockout_Days"] * lost_sales["Daily_Sales_Rate"]).round(0)
                lost_sales["Est_True_Demand"] = (lost_sales["Units_Sold"] + lost_sales["Est_Lost_Sales"]).round(0)
                lost_sales["Lost_Revenue"] = (lost_sales["Est_Lost_Sales"] * lost_sales["Avg_Selling_Price"]).round(0)

                at_risk = lost_sales[lost_sales["Est_Lost_Sales"] > 0].sort_values("Lost_Revenue", ascending=False)

                if len(at_risk) > 0:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        color_metric(len(at_risk), "Products with Possible Lost Sales", "#EF4444")
                    with col2:
                        color_metric(f"{at_risk['Est_Lost_Sales'].sum():,.0f}", "Estimated Lost Units", "#F59E0B")
                    with col3:
                        color_metric(fmt_rs(at_risk['Lost_Revenue'].sum()), "Estimated Lost Revenue", "#EF4444")

                    st.dataframe(
                        at_risk[["Style_No","Product_Name","Category","Color","Units_Sold","Sell_Through","Est_Stockout_Days","Est_Lost_Sales","Est_True_Demand","Lost_Revenue"]].rename(columns={
                            "Style_No":"Style No","Product_Name":"Product",
                            "Units_Sold":"Actual Sales","Sell_Through":"Sold %",
                            "Est_Stockout_Days":"Est Stockout Days","Est_Lost_Sales":"Est Lost Units",
                            "Est_True_Demand":"True Demand Est","Lost_Revenue":"Est Lost Revenue (Rs)"
                        }).reset_index(drop=True),
                        use_container_width=True, hide_index=True,
                        column_config={
                            "Sold %": st.column_config.NumberColumn(format="%.1f%%"),
                            "Est Lost Revenue (Rs)": st.column_config.NumberColumn(format="Rs %d"),
                        }
                    )
                    st.info("💡 These products sold 90%+ of the stock bought, so true demand was likely higher than actual sales. Consider ordering more of these next cycle.")
                else:
                    st.success("✅ No significant stockouts detected in this period.")

        # ── TAB 2 ─────────────────────────────────────
        with tab2:
            st.markdown("<h3 style='color:#FFFFFF'>📦 Stock Status Right Now</h3>", unsafe_allow_html=True)
            st.caption("Sales rates use the last 90 days of your data (or since a product launched). "
                       "Statuses assume each order covers 30 days, with a 95% safety level.")

            inv_status = plan_orders(base, cover_days=30, z=1.65)
            inv_status["Status"] = stock_status(inv_status)
            inv_status["Status_Display"] = inv_status["Status"].apply(status_emoji)
            inv_status["Stock_Value"] = (inv_status["Units_On_Hand"] * inv_status["Cost_Price"]).round(0)
            rate_pos = inv_status["Daily_Sales_Rate"] > 0
            inv_status["Days_of_Stock_Left"] = inv_status["Days_On_Hand"].where(rate_pos).round(0)
            inv_status["Days_Incl_On_Order"] = (inv_status["Stock_Position"] / inv_status["Daily_Sales_Rate"].where(rate_pos)).round(0)
            inv_status["Reorder_In_Days"] = inv_status["Days_Until_Reorder"].where(rate_pos).round(0)
            inv_status["Delivery_Note"] = np.where(inv_status["Delivery_Overdue"], "⚠️ Overdue", "")
            inv_status["Expected_Delivery_Text"] = inv_status["Expected_Delivery_Date"].dt.strftime("%d %b %Y").fillna("—")

            col1, col2, col3, col4, col5, col6 = st.columns(6)
            with col1:
                color_metric(len(inv_status), "Total Products", "#4361EE")
            with col2:
                color_metric(int((inv_status["Status"]=="Out of Stock").sum()), "Out of Stock", "#EF4444")
            with col3:
                color_metric(int((inv_status["Status"]=="Critical").sum()), "Critical", "#F59E0B")
            with col4:
                color_metric(int((inv_status["Status"]=="Not Selling").sum()), "Not Selling", "#AAAAAA")
            with col5:
                color_metric(int((inv_status["Status"]=="Overstock").sum()), "Overstocked", "#60A5FA")
            with col6:
                color_metric(fmt_rs(inv_status['Stock_Value'].sum()), "Stock Value (at cost)", "#10B981")

            st.divider()

            col1, col2, col3 = st.columns(3)
            with col1:
                status_options = ["All"] + list(STATUS_EMOJI.values())
                status_filter = st.selectbox("Stock Status", status_options, key="status1")
            with col2:
                cat_options2 = ["All"] + sorted(inv_status["Category"].dropna().astype(str).unique().tolist())
                cat_filter2 = st.selectbox("Category", cat_options2, key="cat2")
            with col3:
                sort_inv = st.selectbox("Sort By", ["Days of Stock Left","Stock Value","Stock on Hand","Daily Sales Rate"], key="sort2")

            sort_inv_map = {"Days of Stock Left":("Days_Incl_On_Order", True),"Stock Value":("Stock_Value", False),
                            "Stock on Hand":("Units_On_Hand", False),"Daily Sales Rate":("Daily_Sales_Rate", False)}

            filtered_inv = inv_status.copy()
            if status_filter != "All":
                filtered_inv = filtered_inv[filtered_inv["Status_Display"] == status_filter]
            if cat_filter2 != "All":
                filtered_inv = filtered_inv[filtered_inv["Category"].astype(str) == cat_filter2]
            col_, asc_ = sort_inv_map[sort_inv]
            filtered_inv = filtered_inv.sort_values(col_, ascending=asc_, na_position="last")

            filtered_inv_display = filtered_inv.drop(columns=["Status"]).rename(columns={
                "Style_No":"Style No","Product_Name":"Product",
                "Units_On_Hand":"Stock on Hand","Units_On_Order":"On Order",
                "Expected_Delivery_Text":"Expected Delivery","Delivery_Note":"Delivery",
                "Daily_Sales_Rate":"Daily Sales Rate",
                "Days_of_Stock_Left":"Days Left (on hand)","Days_Incl_On_Order":"Days Left (incl. on order)",
                "Reorder_In_Days":"Reorder In",
                "Stock_Value":"Stock Value (Rs, at cost)","Status_Display":"Status"
            })

            st.dataframe(
                filtered_inv_display[["Style No","Product","Status","Stock on Hand","Days Left (on hand)","On Order",
                                      "Days Left (incl. on order)","Reorder In","Expected Delivery","Delivery",
                                      "Daily Sales Rate","Stock Value (Rs, at cost)","Category","Color"]].reset_index(drop=True),
                use_container_width=True, hide_index=True,
                column_config={
                    "Daily Sales Rate": st.column_config.NumberColumn(format="%.2f units/day"),
                    "Days Left (on hand)": st.column_config.NumberColumn(format="%d days"),
                    "Days Left (incl. on order)": st.column_config.NumberColumn(format="%d days"),
                    "Reorder In": st.column_config.NumberColumn(format="%d days", help="Days until stock (incl. on order) reaches the reorder point. 0 = reorder now."),
                    "Stock Value (Rs, at cost)": st.column_config.NumberColumn(format="Rs %d"),
                }
            )
            st.download_button("📥 Download Stock Report", data=to_excel_download(filtered_inv.replace([np.inf, -np.inf], np.nan)), file_name="inventory_status.xlsx")

        # ── TAB 3 ─────────────────────────────────────
        with tab3:
            st.markdown("<h3 style='color:#FFFFFF'>🛒 What Should You Order?</h3>", unsafe_allow_html=True)

            col1, col2, col3 = st.columns(3)
            with col1:
                demand_change = st.selectbox("Expecting demand change?", ["-50%","-30%","-20%","-10%","No change","+10%","+20%","+30%","+50%","+100%"], index=4)
            with col2:
                lead_time_change = st.selectbox("Add delivery buffer (days)", [0,3,5,7,10,14,21,30], index=0,
                    help="Extra days on top of each supplier's usual delivery time, e.g. for festival delays.")
            with col3:
                budget = st.number_input("Your budget (Rs)", min_value=0, value=500000, step=10000)
            col1, col2, col3 = st.columns(3)
            with col1:
                cover_days = st.selectbox("Each order should last (days)", [15, 30, 45, 60, 90], index=1,
                    help="How long stock from this order should last after it arrives — usually the time until your next order.")
            with col2:
                service = st.selectbox("Safety level", list(SERVICE_LEVELS), index=1,
                    help="Chance of not running out while waiting for a delivery. Higher = more buffer stock.")

            demand_map = {"-50%":-0.5,"-30%":-0.3,"-20%":-0.2,"-10%":-0.1,"No change":0,"+10%":0.1,"+20%":0.2,"+30%":0.3,"+50%":0.5,"+100%":1.0}
            demand_pct = demand_map[demand_change]

            reco = plan_orders(base, cover_days=cover_days, demand_pct=demand_pct,
                               extra_lead=lead_time_change, z=SERVICE_LEVELS[service])
            reco["Forecast_Range"] = (reco["Forecast_Lower"].astype(int).astype(str) + " — "
                                      + reco["Forecast_Upper"].astype(int).astype(str) + " units")
            reco["Days_of_Stock_Left"] = reco["Days_On_Hand"].replace(np.inf, np.nan).round(0)

            needs_order = reco[reco["Needs_Order"]].copy()
            needs_order = fit_budget(needs_order, budget) if len(needs_order) else needs_order.assign(In_Budget=[])
            needs_order["Priority_Display"] = needs_order["Priority"].apply(priority_emoji)
            needs_order["Budget_Display"] = np.where(needs_order["In_Budget"], "✅ Order", "⏳ Can wait")
            total_spend = needs_order["Amount_to_Spend"].sum()

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                color_metric(len(needs_order), "Products to Order", "#4361EE")
            with col2:
                color_metric(int((needs_order["Priority"]=="Urgent").sum()), "Urgent", "#EF4444")
            with col3:
                color_metric(fmt_rs(total_spend), "Total to Spend", "#10B981")
            with col4:
                color_metric("✅ Yes" if total_spend <= budget else "❌ No", "Within Budget", "#10B981" if total_spend <= budget else "#EF4444")

            if total_spend > budget and len(needs_order):
                fits = needs_order[needs_order["In_Budget"]]
                waits = needs_order[~needs_order["In_Budget"]]
                st.warning(
                    f"💰 Over budget by Rs {total_spend - budget:,.0f}. To stay within Rs {budget:,.0f}, order the "
                    f"{len(fits)} most urgent products first (Rs {fits['Amount_to_Spend'].sum():,.0f}). "
                    f"The other {len(waits)} (Rs {waits['Amount_to_Spend'].sum():,.0f}) are marked '⏳ Can wait' below — "
                    "urgent items and those running out soonest are kept first."
                )

            coming_up = reco[(~reco["Needs_Order"]) & (reco["Days_Until_Reorder"] <= 14)]
            if len(coming_up):
                st.caption(f"📆 {len(coming_up)} more products will need reordering within the next 2 weeks.")

            st.divider()

            col1, col2, col3 = st.columns(3)
            with col1:
                priority_options = ["All","🔴 Urgent","🟡 Order now"]
                priority_filter = st.selectbox("Priority", priority_options, key="priority1")
            with col2:
                cat_options3 = ["All"] + sorted(needs_order["Category"].dropna().astype(str).unique().tolist())
                cat_filter3 = st.selectbox("Category", cat_options3, key="cat3")
            with col3:
                sort_reco = st.selectbox("Sort By", ["Priority","Amount to Spend","Units to Order","Days of Stock Left"], key="sort3")

            filtered_reco = needs_order.copy()
            if priority_filter != "All":
                filtered_reco = filtered_reco[filtered_reco["Priority_Display"] == priority_filter]
            if cat_filter3 != "All":
                filtered_reco = filtered_reco[filtered_reco["Category"].astype(str) == cat_filter3]
            if sort_reco == "Priority":
                pass  # fit_budget already sorted urgent-first, soonest-to-run-out first
            elif sort_reco == "Days of Stock Left":
                filtered_reco = filtered_reco.sort_values("Days_of_Stock_Left")
            else:
                filtered_reco = filtered_reco.sort_values({"Amount to Spend":"Amount_to_Spend","Units to Order":"Units_to_Order"}[sort_reco], ascending=False)

            filtered_reco_display = filtered_reco.rename(columns={
                "Style_No":"Style No","Product_Name":"Product",
                "Units_On_Hand":"On Hand","Days_of_Stock_Left":"Days of Stock Left",
                "Forecast":f"Forecast ({cover_days} days)","Buffer_Stock":"Buffer Stock",
                "Units_On_Order":"Already Ordered","Units_to_Order":"Order This Many",
                "Amount_to_Spend":"Amount to Spend (Rs)","Priority_Display":"Priority ",
                "Forecast_Range":"Forecast Range","Budget_Display":"Budget Plan"
            })

            if len(filtered_reco):
                st.dataframe(
                    filtered_reco_display[["Style No","Product","Priority ","Order This Many","Amount to Spend (Rs)","Budget Plan",
                                           "On Hand","Already Ordered","Days of Stock Left",
                                           f"Forecast ({cover_days} days)","Forecast Range","Confidence","Buffer Stock",
                                           "Category","Color"]].reset_index(drop=True),
                    use_container_width=True, hide_index=True,
                    column_config={
                        "Amount to Spend (Rs)": st.column_config.NumberColumn(format="Rs %d"),
                        "Days of Stock Left": st.column_config.NumberColumn(format="%d days"),
                    }
                )
                st.download_button("📥 Download Order Plan", data=to_excel_download(filtered_reco.replace([np.inf, -np.inf], np.nan)), file_name="order_plan.xlsx")
            else:
                st.success("✅ Nothing needs ordering right now with these settings.")

            st.divider()
            st.markdown("<h3 style='color:#FFFFFF'>🔍 Why is this the recommendation?</h3>", unsafe_allow_html=True)

            if len(filtered_reco) > 0:
                explain_product = st.selectbox(
                    "Select a product to see the full breakdown",
                    options=filtered_reco["Style_No"].tolist(),
                    format_func=lambda x: str(filtered_reco[filtered_reco["Style_No"]==x]["Product_Name"].values[0]) + " (" + x + ")",
                    key="explain1"
                )

                if explain_product is not None:
                    row = filtered_reco[filtered_reco["Style_No"] == explain_product].iloc[0]
                    rate = row["Adj_Rate"]
                    lead_time = int(row["Adj_Lead"])
                    lead_demand = int(round(row["Lead_Demand"]))
                    cover_demand = int(round(row["Cover_Demand"]))
                    buffer = int(row["Buffer_Stock"])
                    target = int(row["Target_Level"])
                    on_hand = int(row["Units_On_Hand"])
                    on_order = int(row["Units_On_Order"])
                    raw_order = int(row["Raw_Order"])
                    order_qty = int(row["Units_to_Order"])
                    moq = int(row["MOQ"])
                    rop = int(row["Reorder_Point"])
                    days_left = row["Days_of_Stock_Left"]
                    gap = int(row["Stockout_Gap_Days"])
                    amount = int(row["Amount_to_Spend"])
                    product_name = row["Product_Name"]
                    demand_note = f" (includes your {demand_change} demand change)" if demand_pct else ""

                    if row["Priority"] == "Urgent":
                        urgency_msg = (f"Stock lasts about {int(days_left) if pd.notna(days_left) else 0} days but delivery takes {lead_time}. "
                                       f"Even if you order today, expect roughly {gap} days without stock — ask the supplier to rush it if you can.")
                        urgency_color, urgency_icon = "#EF4444", "⚠️"
                    else:
                        urgency_msg = (f"Your stock ({on_hand + on_order} incl. on order) has reached the reorder point of {rop} units — "
                                       f"enough to cover the {lead_time}-day delivery wait plus buffer. Order now so it arrives before you run out.")
                        urgency_color, urgency_icon = "#F59E0B", "🟡"

                    moq_row, moq_warning = "", ""
                    if row["MOQ_Applied"] and raw_order > 0 and moq >= 3 * raw_order and rate > 0:
                        lasts = int((on_hand + on_order + order_qty) / rate)
                        moq_warning = f"""
                        <div style="margin-top:12px; padding:12px; background:#2a2410; border-radius:8px">
                            <p style="color:#F59E0B; margin:0; font-size:14px">⚠️ The supplier minimum ({moq:,}) is {moq / raw_order:.0f}× what you need.
                            This order would last about {lasts} days. Consider negotiating a smaller order or skipping this product.</p>
                        </div>"""
                    if row["MOQ_Applied"]:
                        moq_row = f"""
                            <tr style="border-bottom:1px solid #333">
                                <td style="padding:10px 0; color:#FFFFFF">↑ Rounded up to supplier's minimum order</td>
                                <td style="text-align:right; color:#AAAAAA; font-weight:700">MOQ {moq:,} units</td>
                            </tr>"""

                    st.markdown(f"""
                    <div style="background:#141414; border-radius:12px; padding:24px; border-left:5px solid {urgency_color}; margin-top:16px">
                        <h3 style="color:#FFFFFF; margin:0 0 4px 0">📦 {product_name} ({explain_product})</h3>
                        <p style="color:#AAAAAA; margin:0 0 16px 0; font-size:13px">Selling about {rate:.2f} units/day{demand_note} · forecast confidence: {row['Confidence']}</p>
                        <table style="width:100%; color:#DDDDDD; font-size:15px; border-collapse:collapse">
                            <tr style="border-bottom:1px solid #333">
                                <td style="padding:10px 0; color:#FFFFFF">Sales while waiting for delivery ({lead_time} days)</td>
                                <td style="text-align:right; color:#4361EE; font-weight:700">{lead_demand:,} units</td>
                            </tr>
                            <tr style="border-bottom:1px solid #333">
                                <td style="padding:10px 0; color:#FFFFFF">+ Sales the order must cover ({cover_days} days)</td>
                                <td style="text-align:right; color:#4361EE; font-weight:700">+ {cover_demand:,} units</td>
                            </tr>
                            <tr style="border-bottom:1px solid #333">
                                <td style="padding:10px 0; color:#FFFFFF">+ Buffer stock ({service} safety)</td>
                                <td style="text-align:right; color:#10B981; font-weight:700">+ {buffer:,} units</td>
                            </tr>
                            <tr style="border-bottom:1px solid #333">
                                <td style="padding:10px 0; color:#FFFFFF">= Stock you need in total</td>
                                <td style="text-align:right; color:#FFFFFF; font-weight:700">{target:,} units</td>
                            </tr>
                            <tr style="border-bottom:1px solid #333">
                                <td style="padding:10px 0; color:#FFFFFF">− Stock already on hand</td>
                                <td style="text-align:right; color:#F59E0B; font-weight:700">− {on_hand:,} units</td>
                            </tr>
                            <tr style="border-bottom:1px solid #333">
                                <td style="padding:10px 0; color:#FFFFFF">− Stock already on order</td>
                                <td style="text-align:right; color:#F59E0B; font-weight:700">− {on_order:,} units</td>
                            </tr>
                            <tr style="border-bottom:2px solid #555">
                                <td style="padding:10px 0; color:#FFFFFF">= Shortfall</td>
                                <td style="text-align:right; color:#FFFFFF; font-weight:700">{raw_order:,} units</td>
                            </tr>{moq_row}
                            <tr>
                                <td style="padding:12px 0; font-size:18px; font-weight:700; color:#FFFFFF">✅ Final recommendation</td>
                                <td style="text-align:right; font-size:18px; font-weight:700; color:#FFFFFF">{order_qty:,} units</td>
                            </tr>
                        </table>
                        <div style="margin-top:20px; padding:12px; background:#1C1C1C; border-radius:8px">
                            <p style="color:#AAAAAA; margin:0 0 6px 0; font-size:12px; text-transform:uppercase; letter-spacing:1px">Why order now</p>
                            <p style="color:#FFFFFF; margin:0; font-size:15px">{urgency_icon} {urgency_msg}</p>
                        </div>{moq_warning}
                        <div style="margin-top:12px; padding:12px; background:#1C1C1C; border-radius:8px">
                            <p style="color:#AAAAAA; margin:0 0 6px 0; font-size:12px; text-transform:uppercase; letter-spacing:1px">Cost of this order</p>
                            <p style="color:#10B981; margin:0; font-size:22px; font-weight:700">Rs {amount:,}</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Something went wrong: {str(e)}")
        st.info("Your file needs at least a product code, a sale date and units sold. Download the template for a working example.")

st.divider()
st.caption("🛍️ Retail Inventory Optimiser | Built with Python & Streamlit")
