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
.metric-value { font-size: 28px; font-weight: 700; margin: 8px 0; }
.metric-label { font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 1px; }

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

def to_excel_download(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

def load_data(uploaded_file):
    products = pd.read_excel(uploaded_file, sheet_name="Product_Master")
    uploaded_file.seek(0)
    sales = pd.read_excel(uploaded_file, sheet_name="Sales_History")
    uploaded_file.seek(0)
    inventory = pd.read_excel(uploaded_file, sheet_name="Current_Inventory")
    sales["Date_of_Sale"] = pd.to_datetime(sales["Date_of_Sale"])
    sales["Date_of_Purchase"] = pd.to_datetime(sales["Date_of_Purchase"])
    return products, sales, inventory

def status_emoji(status):
    return {"Out of Stock":"🔴 Out of Stock","Critical":"🟠 Critical","Warning":"🟡 Warning","Healthy":"🟢 Healthy","Overstock":"🔵 Overstock"}.get(status, status)

def priority_emoji(priority):
    return {"Urgent":"🔴 Urgent","Soon":"🟡 Soon","Plan":"🟢 Plan"}.get(priority, priority)

# ── Sidebar ───────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🛍️ Retail Inventory Optimiser")
    st.divider()
    st.markdown("### 📁 Upload Your Data")
    uploaded_file = st.file_uploader("", type=["xlsx","xls"], label_visibility="collapsed")
    st.divider()
    st.markdown("### ⚙️ Store Settings")
    default_lead_time = st.number_input("Supplier delivery time (days)", min_value=1, max_value=90, value=21)
    default_moq = st.number_input("Minimum order quantity", min_value=1, max_value=500, value=60)
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

    demo_safety = round(1.65 * (demo_velocity * 0.3) * (demo_lead ** 0.5))
    demo_reorder = round(demo_velocity * demo_lead + demo_safety)
    demo_days_left = round(demo_stock / demo_velocity) if demo_velocity > 0 else 999
    demo_forecast = round(demo_velocity * 30)
    demo_order = max(60, demo_forecast + demo_safety - demo_stock)

    if demo_days_left < demo_lead:
        demo_status = "🔴 Critical — Order Today"
        demo_color = "#EF4444"
    elif demo_days_left < demo_lead * 1.5:
        demo_status = "🟡 Warning — Order Soon"
        demo_color = "#F59E0B"
    else:
        demo_status = "🟢 Healthy"
        demo_color = "#10B981"

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        color_metric(f"{demo_days_left} days", "Stock Will Last", demo_color)
    with col2:
        color_metric(f"{demo_reorder} units", "Reorder When Stock Hits", "#4361EE")
    with col3:
        color_metric(f"{demo_safety} units", "Buffer Stock Needed", "#F59E0B")
    with col4:
        color_metric(f"{demo_forecast} units", "Forecast Next 30 Days", "#AAAAAA")
    with col5:
        color_metric(f"{demo_order} units", "Recommended Order", "#10B981")

    st.markdown(f"""
    <div style="background:#141414; border:1px solid #222; border-left:5px solid {demo_color}; 
    border-radius:12px; padding:20px; margin-top:16px; text-align:center">
        <div style="font-size:20px; font-weight:700; color:{demo_color}">{demo_status}</div>
        <div style="color:#AAAAAA; margin-top:8px; font-size:14px">
            At {demo_velocity} units/day with {demo_stock} units on hand and {demo_lead} day lead time
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
        today = sales["Date_of_Sale"].max()

        st.markdown("<h1 style='color:#FFFFFF; font-size:36px; font-weight:800'>🛍️ Your Store Dashboard</h1>", unsafe_allow_html=True)
        st.caption(f"📂 {len(products)} products · {len(sales)} sales records · Last sale: {today.strftime('%d %b %Y')}")

        tab1, tab2, tab3 = st.tabs(["📊  Performance", "📦  Inventory Status", "🛒  What to Order"])

        # ── TAB 1 ─────────────────────────────────────
        with tab1:
            st.markdown("<h3 style='color:#FFFFFF'>📊 How Is Your Store Doing?</h3>", unsafe_allow_html=True)

            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                period = st.selectbox("Time Period", ["Last 12 days","Last 30 days","Last 45 days","Last 90 days","All time"])
            with col2:
                win_sellthru = st.selectbox("Winner: Min Sold %", [50,60,70,80,90], index=2)
            with col3:
                win_margin = st.selectbox("Winner: Min Margin %", [20,30,40,50,60], index=2)
            with col4:
                loser_sellthru = st.selectbox("Loser: Max Sold %", [20,30,40,50], index=2)
            with col5:
                sort_by = st.selectbox("Sort By", ["Units Sold","Revenue","Profit","Sold %","Margin %"])

            sort_map = {"Units Sold":"Units_Sold","Revenue":"Revenue","Profit":"Profit","Sold %":"Sell_Through","Margin %":"Avg_Margin"}
            days_map = {"Last 12 days":12,"Last 30 days":30,"Last 45 days":45,"Last 90 days":90,"All time":9999}
            days = days_map[period]
            cutoff = today - timedelta(days=days)
            period_sales = sales[sales["Date_of_Sale"] >= cutoff].copy()

            perf = period_sales.groupby("Style_No").agg(
                Product_Name=("Product_Name","first"), Category=("Category","first"),
                Color=("Color","first"), Gender=("Gender","first"),
                Units_Bought=("Units_Bought","sum"), Units_Sold=("Units_Sold","sum"),
                Revenue=("Revenue","sum"), Profit=("Profit","sum"),
                Avg_Margin=("Margin_Pct","mean"), Avg_Selling_Price=("Selling_Price","mean"),
                MRP=("MRP","first"),
            ).reset_index()

            perf["Sell_Through"] = (perf["Units_Sold"] / perf["Units_Bought"] * 100).round(1)
            perf["Avg_Margin"] = perf["Avg_Margin"].round(1)
            perf["Discount_Taken"] = ((perf["MRP"] - perf["Avg_Selling_Price"]) / perf["MRP"] * 100).round(1)

            def classify(row):
                if row["Sell_Through"] >= win_sellthru and row["Avg_Margin"] >= win_margin:
                    return "🏆 Winner"
                elif row["Sell_Through"] >= win_sellthru and row["Avg_Margin"] < win_margin:
                    return "📈 High Vol Low Margin"
                elif row["Sell_Through"] < loser_sellthru:
                    return "❌ Loser"
                else:
                    return "➡️ Average"

            perf["Tag"] = perf.apply(classify, axis=1)

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                color_metric(f"Rs {perf['Revenue'].sum():,.0f}", "Total Revenue", "#4361EE")
            with col2:
                color_metric(f"Rs {perf['Profit'].sum():,.0f}", "Total Profit", "#10B981")
            with col3:
                color_metric(f"{perf['Sell_Through'].mean():.1f}%", "Avg Sold %", "#F59E0B")
            with col4:
                color_metric(f"{perf['Avg_Margin'].mean():.1f}%", "Avg Margin", "#EF4444")

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
                cat_options = ["All"] + sorted(perf["Category"].dropna().unique().tolist())
                cat_filter = st.selectbox("Category", cat_options, key="cat1")
            with col2:
                gender_options = ["All"] + sorted(perf["Gender"].dropna().unique().tolist())
                gender_filter = st.selectbox("Gender", gender_options, key="gender1")
            with col3:
                tag_options = ["All","🏆 Winner","📈 High Vol Low Margin","➡️ Average","❌ Loser"]
                tag_filter = st.selectbox("Product Tag", tag_options, key="tag1")
            with col4:
                color_options = ["All"] + sorted(perf["Color"].dropna().unique().tolist())
                color_filter = st.selectbox("Colour", color_options, key="colour1")

            filtered_perf = perf.copy()
            if cat_filter != "All":
                filtered_perf = filtered_perf[filtered_perf["Category"] == cat_filter]
            if gender_filter != "All":
                filtered_perf = filtered_perf[filtered_perf["Gender"] == gender_filter]
            if tag_filter != "All":
                filtered_perf = filtered_perf[filtered_perf["Tag"] == tag_filter]
            if color_filter != "All":
                filtered_perf = filtered_perf[filtered_perf["Color"] == color_filter]

            sort_col = sort_map.get(sort_by, "Units_Sold")
            top50 = filtered_perf.nlargest(50, sort_col) if sort_col in filtered_perf.columns else filtered_perf.head(50)

            top50_display = top50.rename(columns={
                "Style_No":"Style No","Product_Name":"Product",
                "Units_Sold":"Units Sold","Sell_Through":"Sold %",
                "Avg_Margin":"Margin %","Discount_Taken":"Discount %","Tag":"Tag"
            })

            st.markdown(f"<p style='color:#FFFFFF; font-weight:600'>Top {min(50, len(top50))} Products</p>", unsafe_allow_html=True)
            st.dataframe(
                top50_display[["Style No","Product","Category","Color","Gender","Units Sold","Sold %","Margin %","Revenue","Profit","Discount %","Tag"]].reset_index(drop=True),
                use_container_width=True,
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
            st.caption("Products that may have sold more if they had not run out of stock")

            lost_sales = perf.copy()
            vel_temp = sales.groupby("Style_No").agg(
                Total_Sold_=("Units_Sold","sum"),
                First_Sale_=("Date_of_Sale","min"),
                Last_Sale_=("Date_of_Sale","max"),
            ).reset_index()
            vel_temp["Selling_Days_"] = ((vel_temp["Last_Sale_"] - vel_temp["First_Sale_"]).dt.days + 1).clip(lower=1)
            vel_temp["Daily_Sales_Rate"] = (vel_temp["Total_Sold_"] / vel_temp["Selling_Days_"]).round(3)
            lost_sales = lost_sales.merge(vel_temp[["Style_No","Daily_Sales_Rate"]], on="Style_No", how="left")

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
                    color_metric(f"Rs {at_risk['Lost_Revenue'].sum():,.0f}", "Estimated Lost Revenue", "#EF4444")

                st.dataframe(
                    at_risk[["Style_No","Product_Name","Category","Color","Units_Sold","Sell_Through","Est_Stockout_Days","Est_Lost_Sales","Est_True_Demand","Lost_Revenue"]].rename(columns={
                        "Style_No":"Style No","Product_Name":"Product",
                        "Units_Sold":"Actual Sales","Sell_Through":"Sold %",
                        "Est_Stockout_Days":"Est Stockout Days","Est_Lost_Sales":"Est Lost Units",
                        "Est_True_Demand":"True Demand Est","Lost_Revenue":"Est Lost Revenue (Rs)"
                    }).reset_index(drop=True),
                    use_container_width=True,
                    column_config={
                        "Sold %": st.column_config.NumberColumn(format="%.1f%%"),
                        "Est Lost Revenue (Rs)": st.column_config.NumberColumn(format="Rs %d"),
                    }
                )
                st.info("💡 These products sold out before the period ended. True demand was likely higher than actual sales. Consider ordering more of these next cycle.")
            else:
                st.success("✅ No significant stockouts detected in this period.")

        # ── TAB 2 ─────────────────────────────────────
        with tab2:
            st.markdown("<h3 style='color:#FFFFFF'>📦 Stock Status Right Now</h3>", unsafe_allow_html=True)

            velocity = sales.groupby("Style_No").agg(
                Product_Name=("Product_Name","first"), Category=("Category","first"),
                Color=("Color","first"), Gender=("Gender","first"),
                Cost_Price=("Cost_Price","first"), Lead_Time=("Lead_Time_Days","first"),
                MOQ=("MOQ","first"), Total_Sold=("Units_Sold","sum"),
                First_Sale=("Date_of_Sale","min"), Last_Sale=("Date_of_Sale","max"),
            ).reset_index()

            velocity["Selling_Days"] = ((velocity["Last_Sale"] - velocity["First_Sale"]).dt.days + 1).clip(lower=1)
            velocity["Daily_Sales_Rate"] = (velocity["Total_Sold"] / velocity["Selling_Days"]).round(3)

            inv_status = velocity.merge(
                inventory[["Style_No","Units_On_Hand","Units_On_Order","Expected_Delivery_Date"]],
                on="Style_No", how="left"
            )
            inv_status["Units_On_Hand"] = inv_status["Units_On_Hand"].fillna(0)
            inv_status["Units_On_Order"] = inv_status["Units_On_Order"].fillna(0)
            inv_status["Days_of_Stock_Left"] = np.where(
                inv_status["Daily_Sales_Rate"] > 0,
                (inv_status["Units_On_Hand"] / inv_status["Daily_Sales_Rate"]).round(0), 999
            )
            inv_status["Stock_Value"] = (inv_status["Units_On_Hand"] * inv_status["Cost_Price"]).round(0)

            def stock_status(row):
                doc = row["Days_of_Stock_Left"]
                lt = row["Lead_Time"]
                if doc == 0: return "Out of Stock"
                elif doc < lt: return "Critical"
                elif doc < lt * 1.5: return "Warning"
                elif doc > lt * 4: return "Overstock"
                else: return "Healthy"

            inv_status["Status"] = inv_status.apply(stock_status, axis=1)
            inv_status["Status_Display"] = inv_status["Status"].apply(status_emoji)

            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                color_metric(len(inv_status), "Total Products", "#4361EE")
            with col2:
                color_metric(int((inv_status["Status"]=="Out of Stock").sum()), "Out of Stock", "#EF4444")
            with col3:
                color_metric(int((inv_status["Status"]=="Critical").sum()), "Critical", "#F59E0B")
            with col4:
                color_metric(int((inv_status["Status"]=="Overstock").sum()), "Overstocked", "#AAAAAA")
            with col5:
                color_metric(f"Rs {inv_status['Stock_Value'].sum():,.0f}", "Stock Value", "#10B981")

            st.divider()

            col1, col2, col3 = st.columns(3)
            with col1:
                status_options = ["All","🔴 Out of Stock","🟠 Critical","🟡 Warning","🟢 Healthy","🔵 Overstock"]
                status_filter = st.selectbox("Stock Status", status_options, key="status1")
            with col2:
                cat_options2 = ["All"] + sorted(inv_status["Category"].dropna().unique().tolist())
                cat_filter2 = st.selectbox("Category", cat_options2, key="cat2")
            with col3:
                sort_inv = st.selectbox("Sort By", ["Days of Stock Left","Stock Value","Stock on Hand","Daily Sales Rate"], key="sort2")

            sort_inv_map = {"Days of Stock Left":"Days_of_Stock_Left","Stock Value":"Stock_Value","Stock on Hand":"Units_On_Hand","Daily Sales Rate":"Daily_Sales_Rate"}

            filtered_inv = inv_status.copy()
            if status_filter != "All":
                status_clean = status_filter.split(" ",1)[1]
                filtered_inv = filtered_inv[filtered_inv["Status"] == status_clean]
            if cat_filter2 != "All":
                filtered_inv = filtered_inv[filtered_inv["Category"] == cat_filter2]
            filtered_inv = filtered_inv.sort_values(sort_inv_map[sort_inv])

            filtered_inv_display = filtered_inv.rename(columns={
                "Style_No":"Style No","Product_Name":"Product",
                "Units_On_Hand":"Stock on Hand","Units_On_Order":"On Order",
                "Expected_Delivery_Date":"Expected Delivery",
                "Daily_Sales_Rate":"Daily Sales Rate",
                "Days_of_Stock_Left":"Days of Stock Left",
                "Stock_Value":"Stock Value (Rs)","Status_Display":"Status"
            })

            st.dataframe(
                filtered_inv_display[["Style No","Product","Category","Color","Stock on Hand","On Order","Expected Delivery","Daily Sales Rate","Days of Stock Left","Stock Value (Rs)","Status"]].reset_index(drop=True),
                use_container_width=True,
                column_config={
                    "Daily Sales Rate": st.column_config.NumberColumn(format="%.2f units/day"),
                    "Days of Stock Left": st.column_config.NumberColumn(format="%d days"),
                    "Stock Value (Rs)": st.column_config.NumberColumn(format="Rs %d"),
                }
            )
            st.download_button("📥 Download Stock Report", data=to_excel_download(filtered_inv), file_name="inventory_status.xlsx")

        # ── TAB 3 ─────────────────────────────────────
        with tab3:
            st.markdown("<h3 style='color:#FFFFFF'>🛒 What Should You Order?</h3>", unsafe_allow_html=True)

            col1, col2, col3 = st.columns(3)
            with col1:
                demand_change = st.selectbox("Expecting demand change?", ["-50%","-30%","-20%","-10%","No change","+10%","+20%","+30%","+50%","+100%"], index=4)
            with col2:
                lead_time_change = st.selectbox("Add delivery buffer (days)", [0,3,5,7,10,14,21,30], index=0)
            with col3:
                budget = st.number_input("Your budget (Rs)", min_value=0, value=500000, step=10000)

            demand_map = {"-50%":-0.5,"-30%":-0.3,"-20%":-0.2,"-10%":-0.1,"No change":0,"+10%":0.1,"+20%":0.2,"+30%":0.3,"+50%":0.5,"+100%":1.0}
            demand_pct = demand_map[demand_change]

            reco = inv_status.copy()
            daily_std = sales.groupby("Style_No")["Units_Sold"].std().fillna(0)
            reco = reco.merge(daily_std.rename("Std_Daily"), on="Style_No", how="left")
            reco["Std_Daily"] = reco["Std_Daily"].fillna(0)

            adj_lead = reco["Lead_Time"] + lead_time_change
            reco["Buffer_Stock"] = (1.65 * reco["Std_Daily"] * np.sqrt(adj_lead)).round(0)
            reco["Order_Trigger"] = (reco["Daily_Sales_Rate"] * adj_lead + reco["Buffer_Stock"]).round(0)
            reco["Forecast_30_Days"] = (reco["Daily_Sales_Rate"] * 30 * (1 + demand_pct)).round(0)
            reco["Forecast_Lower"] = (reco["Forecast_30_Days"] - 1.65 * reco["Std_Daily"] * (30**0.5)).clip(lower=0).round(0)
            reco["Forecast_Upper"] = (reco["Forecast_30_Days"] + 1.65 * reco["Std_Daily"] * (30**0.5)).round(0)
            reco["Forecast_Lower"] = reco["Forecast_Lower"].fillna(0)
            reco["Forecast_Upper"] = reco["Forecast_Upper"].fillna(0)
            reco["CV"] = np.where(reco["Daily_Sales_Rate"] > 0, reco["Std_Daily"] / reco["Daily_Sales_Rate"], 1)
            reco["Confidence"] = np.where(reco["CV"] < 0.2, "🟢 High", np.where(reco["CV"] < 0.5, "🟡 Medium", "🔴 Low"))
            reco["Forecast_Range"] = reco["Forecast_Lower"].astype(int).astype(str) + " — " + reco["Forecast_Upper"].astype(int).astype(str) + " units"
            reco["Units_to_Order"] = (reco["Forecast_30_Days"] + reco["Buffer_Stock"] - reco["Units_On_Hand"] - reco["Units_On_Order"]).clip(lower=0)
            reco["Units_to_Order"] = reco[["Units_to_Order","MOQ"]].max(axis=1).round(0)
            reco["Units_to_Order"] = reco[["Units_to_Order","Order_Trigger"]].max(axis=1).round(0)
            reco["Amount_to_Spend"] = (reco["Units_to_Order"] * reco["Cost_Price"]).round(0)

            needs_order = reco[reco["Units_to_Order"] > 0].copy()

            def priority(row):
                if row["Days_of_Stock_Left"] < row["Lead_Time"]: return "Urgent"
                elif row["Days_of_Stock_Left"] < row["Lead_Time"] * 1.5: return "Soon"
                else: return "Plan"

            needs_order["Priority"] = needs_order.apply(priority, axis=1)
            needs_order["Priority_Display"] = needs_order["Priority"].apply(priority_emoji)
            total_spend = needs_order["Amount_to_Spend"].sum()

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                color_metric(len(needs_order), "Products to Order", "#4361EE")
            with col2:
                color_metric(int((needs_order["Priority"]=="Urgent").sum()), "Order Today", "#EF4444")
            with col3:
                color_metric(f"Rs {total_spend:,.0f}", "Total to Spend", "#10B981")
            with col4:
                color_metric("✅ Yes" if total_spend <= budget else "❌ No", "Within Budget", "#10B981" if total_spend <= budget else "#EF4444")

            st.divider()

            col1, col2, col3 = st.columns(3)
            with col1:
                priority_options = ["All","🔴 Urgent","🟡 Soon","🟢 Plan"]
                priority_filter = st.selectbox("Priority", priority_options, key="priority1")
            with col2:
                cat_options3 = ["All"] + sorted(needs_order["Category"].dropna().unique().tolist())
                cat_filter3 = st.selectbox("Category", cat_options3, key="cat3")
            with col3:
                sort_reco = st.selectbox("Sort By", ["Amount to Spend","Units to Order","Days of Stock Left","Priority"], key="sort3")

            sort_reco_map = {"Amount to Spend":"Amount_to_Spend","Units to Order":"Units_to_Order","Days of Stock Left":"Days_of_Stock_Left","Priority":"Priority"}

            filtered_reco = needs_order.copy()
            if priority_filter != "All":
                priority_clean = priority_filter.split(" ",1)[1]
                filtered_reco = filtered_reco[filtered_reco["Priority"] == priority_clean]
            if cat_filter3 != "All":
                filtered_reco = filtered_reco[filtered_reco["Category"] == cat_filter3]
            filtered_reco = filtered_reco.sort_values(sort_reco_map[sort_reco], ascending=sort_reco != "Priority")

            filtered_reco_display = filtered_reco.rename(columns={
                "Style_No":"Style No","Product_Name":"Product",
                "Units_On_Hand":"Units_On_Hand","Days_of_Stock_Left":"Days of Stock Left",
                "Forecast_30_Days":"Forecast (30 days)","Buffer_Stock":"Buffer Stock",
                "Units_On_Order":"Already Ordered","Units_to_Order":"Order This Many",
                "Amount_to_Spend":"Amount to Spend (Rs)","Priority_Display":"Priority",
                "Forecast_Range":"Forecast Range","Confidence":"Confidence"
            })

            st.dataframe(
                filtered_reco_display[["Style No","Product","Category","Color","Units_On_Hand","Days of Stock Left","Forecast (30 days)","Forecast Range","Confidence","Buffer Stock","Already Ordered","Order This Many","Amount to Spend (Rs)","Priority"]].reset_index(drop=True),
                use_container_width=True,
                column_config={
                    "Amount to Spend (Rs)": st.column_config.NumberColumn(format="Rs %d"),
                    "Days of Stock Left": st.column_config.NumberColumn(format="%d days"),
                }
            )
            st.download_button("📥 Download Order Plan", data=to_excel_download(filtered_reco), file_name="order_plan.xlsx")

            st.divider()
            st.markdown("<h3 style='color:#FFFFFF'>🔍 Why is this the recommendation?</h3>", unsafe_allow_html=True)

            if len(filtered_reco) > 0:
                explain_product = st.selectbox(
                    "Select a product to see the full breakdown",
                    options=filtered_reco["Style_No"].tolist(),
                    format_func=lambda x: filtered_reco[filtered_reco["Style_No"]==x]["Product_Name"].values[0] + " (" + x + ")",
                    key="explain1"
                )

                if explain_product is not None:
                    row = filtered_reco[filtered_reco["Style_No"] == explain_product].iloc[0]
                    forecast = int(row["Forecast_30_Days"])
                    buffer = int(row["Buffer_Stock"])
                    on_hand = int(row["Units_On_Hand"])
                    on_order = int(row["Already Ordered"])
                    order_qty = int(row["Order This Many"])
                    days_left = int(row["Days of Stock Left"])
                    lead_time = int(row["Lead_Time"])
                    amount = int(row["Amount to Spend (Rs)"])
                    priority_val = row["Priority"]
                    product_name = row["Product"]
                    raw_order = max(forecast + buffer - on_hand - on_order, 0)

                    if priority_val == "Urgent":
                        urgency_msg = f"Stock will last {days_left} days. Supplier takes {lead_time} days. You will run out before delivery arrives. Order today."
                        urgency_color = "#EF4444"
                        urgency_icon = "⚠️"
                    elif priority_val == "Soon":
                        urgency_msg = f"Stock will last {days_left} days. Supplier takes {lead_time} days. Order this week to stay safe."
                        urgency_color = "#F59E0B"
                        urgency_icon = "🟡"
                    else:
                        urgency_msg = f"Stock will last {days_left} days. Supplier takes {lead_time} days. You have time but plan ahead."
                        urgency_color = "#10B981"
                        urgency_icon = "🟢"

                    st.markdown(f"""
                    <div style="background:#141414; border-radius:12px; padding:24px; border-left:5px solid {urgency_color}; margin-top:16px">
                        <h3 style="color:#FFFFFF; margin:0 0 16px 0">📦 {product_name} ({explain_product})</h3>
                        <table style="width:100%; color:#DDDDDD; font-size:15px; border-collapse:collapse">
                            <tr style="border-bottom:1px solid #333">
                                <td style="padding:10px 0; color:#FFFFFF">Forecast demand (next 30 days)</td>
                                <td style="text-align:right; color:#4361EE; font-weight:700">{forecast:,} units</td>
                            </tr>
                            <tr style="border-bottom:1px solid #333">
                                <td style="padding:10px 0; color:#FFFFFF">+ Buffer stock needed</td>
                                <td style="text-align:right; color:#10B981; font-weight:700">+ {buffer:,} units</td>
                            </tr>
                            <tr style="border-bottom:1px solid #333">
                                <td style="padding:10px 0; color:#FFFFFF">- Stock already on hand</td>
                                <td style="text-align:right; color:#F59E0B; font-weight:700">- {on_hand:,} units</td>
                            </tr>
                            <tr style="border-bottom:1px solid #333">
                                <td style="padding:10px 0; color:#FFFFFF">- Stock already on order</td>
                                <td style="text-align:right; color:#F59E0B; font-weight:700">- {on_order:,} units</td>
                            </tr>
                            <tr style="border-bottom:2px solid #555">
                                <td style="padding:10px 0; color:#FFFFFF">Raw order quantity</td>
                                <td style="text-align:right; color:#FFFFFF; font-weight:700">{raw_order:,} units</td>
                            </tr>
                            <tr>
                                <td style="padding:12px 0; font-size:18px; font-weight:700; color:#FFFFFF">✅ Final recommendation</td>
                                <td style="text-align:right; font-size:18px; font-weight:700; color:#FFFFFF">{order_qty:,} units</td>
                            </tr>
                        </table>
                        <div style="margin-top:20px; padding:12px; background:#1C1C1C; border-radius:8px">
                            <p style="color:#AAAAAA; margin:0 0 6px 0; font-size:12px; text-transform:uppercase; letter-spacing:1px">Why this recommendation</p>
                            <p style="color:#FFFFFF; margin:0; font-size:15px">{urgency_icon} {urgency_msg}</p>
                        </div>
                        <div style="margin-top:12px; padding:12px; background:#1C1C1C; border-radius:8px">
                            <p style="color:#AAAAAA; margin:0 0 6px 0; font-size:12px; text-transform:uppercase; letter-spacing:1px">Cost of this order</p>
                            <p style="color:#10B981; margin:0; font-size:22px; font-weight:700">Rs {amount:,}</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Something went wrong: {str(e)}")
        st.info("Make sure your file has 3 sheets: Product_Master, Sales_History, Current_Inventory")

st.divider()
st.caption("🛍️ Retail Inventory Optimiser | Built with Python & Streamlit")
