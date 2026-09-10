import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

st.set_page_config(page_title="Retail Inventory Optimiser", page_icon="🛍️", layout="wide")

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

# ── Sidebar ───────────────────────────────────────────
with st.sidebar:
    st.title("Retail Inventory Optimiser")
    st.divider()
    st.subheader("Upload Your Data")
    uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx","xls"])
    st.divider()
    st.subheader("Default Settings")
    default_lead_time = st.number_input("Lead time (days)", min_value=1, max_value=90, value=21)
    default_moq = st.number_input("Minimum order quantity", min_value=1, max_value=500, value=60)
    st.divider()
    template_path = "data/raw/retailer_template.xlsx"
    with open(template_path, "rb") as f:
        st.download_button("Download Template", data=f.read(), file_name="retailer_template.xlsx")

# ── Landing page ──────────────────────────────────────
if uploaded_file is None:
    st.title("Retail Inventory Optimiser")
    st.subheader("Help small retailers understand their store and plan future buying")
    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 📊 Performance")
        st.markdown("See your top sellers, margins, and winners vs losers")
    with col2:
        st.markdown("### 📦 Inventory")
        st.markdown("Live stock status — what you have and how long it will last")
    with col3:
        st.markdown("### 🛒 Order")
        st.markdown("Exactly what to order, how much, and when")
    st.divider()
    st.markdown("### Required Excel Format — 3 Sheets")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**Sheet 1 — Product_Master**")
        st.dataframe(pd.DataFrame({
            "Column": ["Style_No","Article_No","Product_Name","Category","Color","Gender","Cost_Price","MRP","Lead_Time_Days","MOQ"],
            "Required": ["Yes","Yes","Yes","Yes","No","No","Yes","Yes","No","No"],
            "Example": ["ST001","ART001","Blue Slim Jeans","Jeans","Blue","Men","450","999","21","60"]
        }), hide_index=True, use_container_width=True)
    with col2:
        st.markdown("**Sheet 2 — Sales_History**")
        st.dataframe(pd.DataFrame({
            "Column": ["Style_No","Date_of_Purchase","Date_of_Sale","Units_Bought","Units_Sold","Selling_Price"],
            "Required": ["Yes","Yes","Yes","Yes","Yes","Yes"],
            "Example": ["ST001","2026-01-01","2026-01-15","120","88","899"]
        }), hide_index=True, use_container_width=True)
    with col3:
        st.markdown("**Sheet 3 — Current_Inventory**")
        st.dataframe(pd.DataFrame({
            "Column": ["Style_No","Units_On_Hand","Units_On_Order","Expected_Delivery_Date"],
            "Required": ["Yes","Yes","No","No"],
            "Example": ["ST001","45","60","2026-09-05"]
        }), hide_index=True, use_container_width=True)
    st.info("Download the template, fill in your data, and upload it to get started")

else:
    try:
        products, sales, inventory = load_data(uploaded_file)

        # Merge all data
        sales = sales.merge(products[["Style_No","Product_Name","Category","Color","Gender","Cost_Price","MRP","Lead_Time_Days","MOQ"]], on="Style_No", how="left")
        sales["Lead_Time_Days"] = sales["Lead_Time_Days"].fillna(default_lead_time)
        sales["MOQ"] = sales["MOQ"].fillna(default_moq)
        sales["Margin_Pct"] = ((sales["Selling_Price"] - sales["Cost_Price"]) / sales["Selling_Price"] * 100).round(1)
        sales["Revenue"] = sales["Units_Sold"] * sales["Selling_Price"]
        sales["Profit"] = sales["Units_Sold"] * (sales["Selling_Price"] - sales["Cost_Price"])

        today = sales["Date_of_Sale"].max()

        st.title("Retail Inventory Optimiser")
        st.caption(f"Data loaded: {len(products)} products | {len(sales)} sales records | Stock snapshot as of today")

        tab1, tab2, tab3 = st.tabs(["📊 Performance Analysis", "📦 Inventory Status", "🛒 Order Recommendations"])

        # ── TAB 1: PERFORMANCE ANALYSIS ───────────────
        with tab1:
            st.subheader("Performance Analysis")

            # Controls
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                period = st.selectbox("Time period", ["Last 12 days","Last 30 days","Last 45 days","Last 90 days","All time"])
            with col2:
                win_sellthru = st.slider("Winner sell through threshold (%)", 0, 100, 70)
            with col3:
                win_margin = st.slider("Winner margin threshold (%)", 0, 100, 40)
            with col4:
                loser_sellthru = st.slider("Loser sell through threshold (%)", 0, 100, 40)

            # Filter by period
            days_map = {"Last 12 days": 12, "Last 30 days": 30, "Last 45 days": 45, "Last 90 days": 90, "All time": 9999}
            days = days_map[period]
            cutoff = today - timedelta(days=days)
            period_sales = sales[sales["Date_of_Sale"] >= cutoff].copy()

            # Aggregate per article
            perf = period_sales.groupby("Style_No").agg(
                Product_Name=("Product_Name","first"),
                Category=("Category","first"),
                Color=("Color","first"),
                Gender=("Gender","first"),
                Units_Bought=("Units_Bought","sum"),
                Units_Sold=("Units_Sold","sum"),
                Revenue=("Revenue","sum"),
                Profit=("Profit","sum"),
                Avg_Margin=("Margin_Pct","mean"),
                Avg_Selling_Price=("Selling_Price","mean"),
                MRP=("MRP","first"),
            ).reset_index()

            perf["Sell_Through"] = (perf["Units_Sold"] / perf["Units_Bought"] * 100).round(1)
            perf["Avg_Margin"] = perf["Avg_Margin"].round(1)
            perf["Discount_Taken"] = ((perf["MRP"] - perf["Avg_Selling_Price"]) / perf["MRP"] * 100).round(1)

            # Classify
            def classify(row):
                if row["Sell_Through"] >= win_sellthru and row["Avg_Margin"] >= win_margin:
                    return "Winner"
                elif row["Sell_Through"] >= win_sellthru and row["Avg_Margin"] < win_margin:
                    return "High Volume Low Margin"
                elif row["Sell_Through"] < loser_sellthru:
                    return "Loser"
                else:
                    return "Average"

            perf["Classification"] = perf.apply(classify, axis=1)

            # Top metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Revenue", f"Rs {perf['Revenue'].sum():,.0f}")
            with col2:
                st.metric("Total Profit", f"Rs {perf['Profit'].sum():,.0f}")
            with col3:
                st.metric("Avg Sell Through", f"{perf['Sell_Through'].mean():.1f}%")
            with col4:
                st.metric("Avg Margin", f"{perf['Avg_Margin'].mean():.1f}%")

            st.divider()

            # Classification summary
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                winners = (perf["Classification"] == "Winner").sum()
                st.metric("Winners", winners, delta="reorder these")
            with col2:
                losers = (perf["Classification"] == "Loser").sum()
                st.metric("Losers", losers, delta="consider killing", delta_color="inverse")
            with col3:
                hvlm = (perf["Classification"] == "High Volume Low Margin").sum()
                st.metric("High Vol Low Margin", hvlm)
            with col4:
                avg = (perf["Classification"] == "Average").sum()
                st.metric("Average", avg)

            st.divider()

            # Filters
            col1, col2, col3 = st.columns(3)
            with col1:
                cat_filter = st.multiselect("Category", options=sorted(perf["Category"].dropna().unique()), default=[])
            with col2:
                gender_filter = st.multiselect("Gender", options=sorted(perf["Gender"].dropna().unique()), default=[])
            with col3:
                class_filter = st.multiselect("Classification", options=["Winner","High Volume Low Margin","Average","Loser"], default=[])

            filtered_perf = perf.copy()
            if cat_filter:
                filtered_perf = filtered_perf[filtered_perf["Category"].isin(cat_filter)]
            if gender_filter:
                filtered_perf = filtered_perf[filtered_perf["Gender"].isin(gender_filter)]
            if class_filter:
                filtered_perf = filtered_perf[filtered_perf["Classification"].isin(class_filter)]

            # Top 50
            top50 = filtered_perf.nlargest(50, "Units_Sold")

            st.markdown(f"**Top {min(50, len(top50))} Articles by Units Sold**")
            st.dataframe(
                top50[["Style_No","Product_Name","Category","Color","Gender","Units_Sold","Sell_Through","Avg_Margin","Revenue","Profit","Discount_Taken","Classification"]].reset_index(drop=True),
                use_container_width=True,
                column_config={
                    "Sell_Through": st.column_config.NumberColumn("Sell Through %", format="%.1f%%"),
                    "Avg_Margin": st.column_config.NumberColumn("Margin %", format="%.1f%%"),
                    "Discount_Taken": st.column_config.NumberColumn("Discount Taken %", format="%.1f%%"),
                    "Revenue": st.column_config.NumberColumn("Revenue (Rs)", format="Rs %d"),
                    "Profit": st.column_config.NumberColumn("Profit (Rs)", format="Rs %d"),
                }
            )

            col1, col2 = st.columns(2)
            with col1:
                st.download_button("Download Performance Report", data=to_excel_download(top50), file_name="performance_report.xlsx")
            with col2:
                # Classification chart
                class_counts = perf["Classification"].value_counts()
                fig, ax = plt.subplots(figsize=(6,3))
                colors = {"Winner":"green","High Volume Low Margin":"orange","Average":"steelblue","Loser":"red"}
                bars = ax.bar(class_counts.index, class_counts.values, color=[colors.get(c,"grey") for c in class_counts.index])
                ax.set_title("Articles by Classification")
                ax.set_ylabel("Number of Articles")
                plt.xticks(rotation=15, ha="right")
                plt.tight_layout()
                st.pyplot(fig)
                plt.close()

        # ── TAB 2: INVENTORY STATUS ────────────────────
        with tab2:
            st.subheader("Inventory Status — Right Now")

            # Calculate velocity from all sales
            velocity = sales.groupby("Style_No").agg(
                Product_Name=("Product_Name","first"),
                Category=("Category","first"),
                Color=("Color","first"),
                Gender=("Gender","first"),
                Cost_Price=("Cost_Price","first"),
                Lead_Time=("Lead_Time_Days","first"),
                MOQ=("MOQ","first"),
                Total_Sold=("Units_Sold","sum"),
                First_Sale=("Date_of_Sale","min"),
                Last_Sale=("Date_of_Sale","max"),
            ).reset_index()

            velocity["Selling_Days"] = ((velocity["Last_Sale"] - velocity["First_Sale"]).dt.days + 1).clip(lower=1)
            velocity["Daily_Velocity"] = (velocity["Total_Sold"] / velocity["Selling_Days"]).round(3)

            # Merge with current inventory
            inv_status = velocity.merge(inventory[["Style_No","Units_On_Hand","Units_On_Order","Expected_Delivery_Date"]], on="Style_No", how="left")
            inv_status["Units_On_Hand"] = inv_status["Units_On_Hand"].fillna(0)
            inv_status["Units_On_Order"] = inv_status["Units_On_Order"].fillna(0)

            # Days of cover
            inv_status["Days_of_Cover"] = np.where(
                inv_status["Daily_Velocity"] > 0,
                (inv_status["Units_On_Hand"] / inv_status["Daily_Velocity"]).round(0),
                999
            )

            # Stock value
            inv_status["Stock_Value"] = (inv_status["Units_On_Hand"] * inv_status["Cost_Price"]).round(0)

            # Status classification
            def stock_status(row):
                doc = row["Days_of_Cover"]
                lt = row["Lead_Time"]
                if doc == 0:
                    return "Out of Stock"
                elif doc < lt:
                    return "Critical"
                elif doc < lt * 1.5:
                    return "Warning"
                elif doc > lt * 4:
                    return "Overstock"
                else:
                    return "Healthy"

            inv_status["Status"] = inv_status.apply(stock_status, axis=1)

            # Summary metrics
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("Total SKUs", len(inv_status))
            with col2:
                st.metric("Out of Stock", int((inv_status["Status"] == "Out of Stock").sum()), delta_color="inverse")
            with col3:
                st.metric("Critical", int((inv_status["Status"] == "Critical").sum()), delta_color="inverse")
            with col4:
                st.metric("Overstock", int((inv_status["Status"] == "Overstock").sum()), delta_color="inverse")
            with col5:
                st.metric("Total Stock Value", f"Rs {inv_status['Stock_Value'].sum():,.0f}")

            st.divider()

            # Filters
            col1, col2 = st.columns(2)
            with col1:
                status_filter = st.multiselect("Filter by status", options=["Out of Stock","Critical","Warning","Healthy","Overstock"], default=["Out of Stock","Critical"])
            with col2:
                cat_filter2 = st.multiselect("Filter by category", options=sorted(inv_status["Category"].dropna().unique()), default=[])

            filtered_inv = inv_status.copy()
            if status_filter:
                filtered_inv = filtered_inv[filtered_inv["Status"].isin(status_filter)]
            if cat_filter2:
                filtered_inv = filtered_inv[filtered_inv["Category"].isin(cat_filter2)]

            st.dataframe(
                filtered_inv[["Style_No","Product_Name","Category","Color","Gender","Units_On_Hand","Units_On_Order","Expected_Delivery_Date","Daily_Velocity","Days_of_Cover","Stock_Value","Status"]].sort_values("Days_of_Cover").reset_index(drop=True),
                use_container_width=True,
                column_config={
                    "Daily_Velocity": st.column_config.NumberColumn("Daily Velocity", format="%.2f"),
                    "Stock_Value": st.column_config.NumberColumn("Stock Value (Rs)", format="Rs %d"),
                    "Days_of_Cover": st.column_config.NumberColumn("Days of Cover", format="%d days"),
                }
            )

            st.download_button("Download Inventory Report", data=to_excel_download(filtered_inv), file_name="inventory_status.xlsx")

            # Status distribution chart
            status_counts = inv_status["Status"].value_counts()
            fig, ax = plt.subplots(figsize=(8,3))
            status_colors = {"Out of Stock":"red","Critical":"orange","Warning":"yellow","Healthy":"green","Overstock":"purple"}
            ax.bar(status_counts.index, status_counts.values, color=[status_colors.get(s,"grey") for s in status_counts.index])
            ax.set_title("Stock Status Distribution")
            ax.set_ylabel("Number of SKUs")
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

        # ── TAB 3: ORDER RECOMMENDATIONS ──────────────
        with tab3:
            st.subheader("Order Recommendations")

            # What-if controls
            col1, col2, col3 = st.columns(3)
            with col1:
                demand_change = st.slider("Expected demand change (%)", -50, 100, 0, 5)
            with col2:
                lead_time_change = st.slider("Lead time buffer (days)", 0, 30, 0, 1)
            with col3:
                budget = st.number_input("Budget limit (Rs)", min_value=0, value=500000, step=10000)

            # Calculate recommendations using velocity from Tab 2
            reco = inv_status.copy()

            # Daily std for safety stock
            daily_std = sales.groupby("Style_No")["Units_Sold"].std().fillna(0)
            reco = reco.merge(daily_std.rename("Std_Daily"), on="Style_No", how="left")
            reco["Std_Daily"] = reco["Std_Daily"].fillna(0)

            adj_lead = reco["Lead_Time"] + lead_time_change
            reco["Safety_Stock"] = (1.65 * reco["Std_Daily"] * np.sqrt(adj_lead)).round(0)
            reco["Reorder_Point"] = (reco["Daily_Velocity"] * adj_lead + reco["Safety_Stock"]).round(0)
            reco["Forecast_30_Days"] = (reco["Daily_Velocity"] * 30 * (1 + demand_change/100)).round(0)
            reco["Order_Qty"] = (reco["Forecast_30_Days"] + reco["Safety_Stock"] - reco["Units_On_Hand"] - reco["Units_On_Order"]).clip(lower=0)
            reco["Order_Qty"] = reco[["Order_Qty","MOQ"]].max(axis=1).round(0)
            reco["Order_Qty"] = reco[["Order_Qty","Reorder_Point"]].max(axis=1).round(0)
            reco["Working_Capital"] = (reco["Order_Qty"] * reco["Cost_Price"]).round(0)

            # Only show items that need ordering
            needs_order = reco[reco["Order_Qty"] > 0].copy()

            # Priority
            def priority(row):
                if row["Days_of_Cover"] < row["Lead_Time"]:
                    return "Urgent"
                elif row["Days_of_Cover"] < row["Lead_Time"] * 1.5:
                    return "Soon"
                else:
                    return "Plan"

            needs_order["Priority"] = needs_order.apply(priority, axis=1)

            # Summary
            total_wc = needs_order["Working_Capital"].sum()
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("SKUs to Order", len(needs_order))
            with col2:
                st.metric("Urgent", int((needs_order["Priority"] == "Urgent").sum()), delta_color="inverse")
            with col3:
                st.metric("Total Working Capital", f"Rs {total_wc:,.0f}")
            with col4:
                within_budget = total_wc <= budget
                st.metric("Within Budget", "Yes" if within_budget else "No")

            st.divider()

            # Priority filter
            priority_filter = st.multiselect("Filter by priority", options=["Urgent","Soon","Plan"], default=["Urgent","Soon"])
            filtered_reco = needs_order[needs_order["Priority"].isin(priority_filter)] if priority_filter else needs_order

            st.dataframe(
                filtered_reco[["Style_No","Product_Name","Category","Color","Units_On_Hand","Days_of_Cover","Forecast_30_Days","Safety_Stock","Units_On_Order","Order_Qty","Working_Capital","Priority"]].sort_values(["Priority","Days_of_Cover"]).reset_index(drop=True),
                use_container_width=True,
                column_config={
                    "Working_Capital": st.column_config.NumberColumn("Working Capital (Rs)", format="Rs %d"),
                    "Days_of_Cover": st.column_config.NumberColumn("Days of Cover", format="%d days"),
                }
            )

            st.download_button("Download Order Plan", data=to_excel_download(filtered_reco), file_name="order_plan.xlsx")

    except Exception as e:
        st.error(f"Error: {str(e)}")
        st.info("Make sure your file has sheets named Product_Master, Sales_History and Current_Inventory")

st.caption("Retail Inventory Optimiser | Built with Python, Pandas, Streamlit")
