import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

st.set_page_config(
    page_title="Retail Inventory Optimiser",
    page_icon="🛍️",
    layout="wide"
)

def apply_theme(theme):
    if theme == "Dark":
        st.markdown("""
        <style>
        .stApp { background-color: #111111; }
        .main { background-color: #111111; }
        h1, h2, h3, h4, p, label { color: #FFFFFF !important; }
        .metric-card {
            background: #1C1C1C;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            margin: 4px;
            border: 1px solid #2A2A2A;
        }
        .metric-value {
            font-size: 30px;
            font-weight: 700;
            margin: 8px 0;
        }
        .metric-label {
            font-size: 12px;
            color: #AAAAAA;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        div[data-testid="metric-container"] {
            background: #1C1C1C;
            border: 1px solid #2A2A2A;
            border-radius: 12px;
            padding: 15px;
        }
        .stDataFrame { border-radius: 8px; }
        .stSelectbox label { color: #FFFFFF !important; }
        .stNumberInput label { color: #FFFFFF !important; }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
        .stApp { background-color: #FFFFFF; }
        .main { background-color: #FFFFFF; }
        h1, h2, h3, h4, p, label { color: #111111 !important; }
        .metric-card {
            background: #F5F5F5;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            margin: 4px;
            border: 1px solid #E0E0E0;
        }
        .metric-value {
            font-size: 30px;
            font-weight: 700;
            margin: 8px 0;
        }
        .metric-label {
            font-size: 12px;
            color: #666666;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        div[data-testid="metric-container"] {
            background: #F5F5F5;
            border: 1px solid #E0E0E0;
            border-radius: 12px;
            padding: 15px;
        }
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
    st.markdown("*Smart buying decisions for your store*")
    st.divider()
    st.markdown("### 📁 Upload Your Data")
    uploaded_file = st.file_uploader("", type=["xlsx","xls"], label_visibility="collapsed")
    st.divider()
    st.markdown("### ⚙️ Store Settings")
    default_lead_time = st.number_input("Supplier delivery time (days)", min_value=1, max_value=90, value=21)
    default_moq = st.number_input("Minimum order quantity", min_value=1, max_value=500, value=60)
    st.divider()
    st.markdown("### 🎨 Appearance")
    theme = st.selectbox("Theme", ["Dark", "Light"], index=0)
    st.divider()
    st.markdown("### 📥 New here?")
    template_path = "data/raw/retailer_template.xlsx"
    try:
        with open(template_path, "rb") as f:
            st.download_button("⬇️ Download Excel Template", data=f.read(), file_name="retailer_template.xlsx", use_container_width=True)
    except:
        st.info("Template not found")

apply_theme(theme)

# ── Landing page ──────────────────────────────────────
if uploaded_file is None:
    st.markdown("<h1 style='text-align:center; font-size:48px'>🛍️ Retail Inventory Optimiser</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; font-size:20px; color:#AAAAAA'>Know what to buy, how much, and when — in seconds</p>", unsafe_allow_html=True)
    st.divider()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""<div style="background:#1C1C1C; border-radius:16px; padding:30px; text-align:center; border-left:5px solid #4361EE">
        <div style="font-size:40px">📊</div>
        <h3 style="color:#4361EE">Performance</h3>
        <p style="color:#AAAAAA">See your best and worst selling products. Know what to reorder and what to cut.</p>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown("""<div style="background:#1C1C1C; border-radius:16px; padding:30px; text-align:center; border-left:5px solid #10B981">
        <div style="font-size:40px">📦</div>
        <h3 style="color:#10B981">Inventory</h3>
        <p style="color:#AAAAAA">See how much stock you have and how many days it will last at current sales rate.</p>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown("""<div style="background:#1C1C1C; border-radius:16px; padding:30px; text-align:center; border-left:5px solid #F59E0B">
        <div style="font-size:40px">🛒</div>
        <h3 style="color:#F59E0B">Orders</h3>
        <p style="color:#AAAAAA">Get exact quantities to order for each product with total cost estimates.</p>
        </div>""", unsafe_allow_html=True)

    st.divider()
    st.markdown("<h3 style='text-align:center'>👈 Upload your Excel file from the sidebar to get started</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#AAAAAA'>Download the template, fill in your store data, and upload it</p>", unsafe_allow_html=True)
    st.divider()

    st.markdown("### 📋 What goes in your Excel file?")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**Sheet 1 — Your Products**")
        st.dataframe(pd.DataFrame({
            "Column": ["Style_No","Article_No","Product_Name","Category","Color","Gender","Cost_Price","MRP","Lead_Time_Days","MOQ"],
            "Needed": ["✅","✅","✅","✅","⬜","⬜","✅","✅","⬜","⬜"],
            "Example": ["ST001","ART001","Blue Slim Jeans","Jeans","Blue","Men","450","999","21","60"]
        }), hide_index=True, use_container_width=True)
    with col2:
        st.markdown("**Sheet 2 — Your Sales**")
        st.dataframe(pd.DataFrame({
            "Column": ["Style_No","Date_of_Purchase","Date_of_Sale","Units_Bought","Units_Sold","Selling_Price"],
            "Needed": ["✅","✅","✅","✅","✅","✅"],
            "Example": ["ST001","2026-01-01","2026-01-15","120","88","899"]
        }), hide_index=True, use_container_width=True)
    with col3:
        st.markdown("**Sheet 3 — Current Stock**")
        st.dataframe(pd.DataFrame({
            "Column": ["Style_No","Units_On_Hand","Units_On_Order","Expected_Delivery_Date"],
            "Needed": ["✅","✅","⬜","⬜"],
            "Example": ["ST001","45","60","2026-09-05"]
        }), hide_index=True, use_container_width=True)

else:
    try:
        products, sales, inventory = load_data(uploaded_file)
        sales = sales.merge(products[["Style_No","Product_Name","Category","Color","Gender","Cost_Price","MRP","Lead_Time_Days","MOQ"]], on="Style_No", how="left")
        sales["Lead_Time_Days"] = sales["Lead_Time_Days"].fillna(default_lead_time)
        sales["MOQ"] = sales["MOQ"].fillna(default_moq)
        sales["Margin_Pct"] = ((sales["Selling_Price"] - sales["Cost_Price"]) / sales["Selling_Price"] * 100).round(1)
        sales["Revenue"] = sales["Units_Sold"] * sales["Selling_Price"]
        sales["Profit"] = sales["Units_Sold"] * (sales["Selling_Price"] - sales["Cost_Price"])
        today = sales["Date_of_Sale"].max()

        st.markdown("<h1>🛍️ Your Store Dashboard</h1>", unsafe_allow_html=True)
        st.caption(f"📂 {len(products)} products · {len(sales)} sales records · Last sale: {today.strftime('%d %b %Y')}")

        tab1, tab2, tab3 = st.tabs(["📊  Performance", "📦  Inventory Status", "🛒  What to Order"])

        # ── TAB 1 ─────────────────────────────────────
        with tab1:
            st.markdown("### 📊 How Is Your Store Doing?")

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

            st.markdown(f"**Top {min(50, len(top50))} Products**")
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

        # ── TAB 2 ─────────────────────────────────────
        with tab2:
            st.markdown("### 📦 Stock Status Right Now")

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
                filtered_inv_display[["Style No","Product","Category","Color","Stock on Hand","On Order","Expected Delivery","Daily Sales Rate","Days of Stock Left","Stock Value (Rs)"]].reset_index(drop=True),
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
            st.markdown("### 🛒 What Should You Order?")

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
                "Units_On_Hand":"Stock on Hand","Days_of_Stock_Left":"Days of Stock Left",
                "Forecast_30_Days":"Forecast (30 days)","Buffer_Stock":"Buffer Stock",
                "Units_On_Order":"Already Ordered","Units_to_Order":"Order This Many",
                "Amount_to_Spend":"Amount to Spend (Rs)","Priority_Display":"Priority"
            })

            st.dataframe(
                filtered_reco_display[["Style No","Product","Category","Color","Stock on Hand","Days of Stock Left","Forecast (30 days)","Buffer Stock","Already Ordered","Order This Many","Amount to Spend (Rs)"]].reset_index(drop=True),
                use_container_width=True,
                column_config={
                    "Amount to Spend (Rs)": st.column_config.NumberColumn(format="Rs %d"),
                    "Days of Stock Left": st.column_config.NumberColumn(format="%d days"),
                }
            )
            st.download_button("📥 Download Order Plan", data=to_excel_download(filtered_reco), file_name="order_plan.xlsx")

    except Exception as e:
        st.error(f"Something went wrong: {str(e)}")
        st.info("Make sure your file has 3 sheets: Product_Master, Sales_History, Current_Inventory")

st.divider()
st.caption("🛍️ Retail Inventory Optimiser | Built with Python & Streamlit")
