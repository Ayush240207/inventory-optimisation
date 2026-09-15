# Retail Inventory Optimiser — Project Brief

## What This Project Is
A universal inventory optimisation tool for small retail businesses.
Any retailer uploads their sales data and instantly gets recommendations
on what to order, how much, and how urgently.

## How To Run
conda activate inventory-project
cd ~/inventory-optimisation
streamlit run app/dashboard.py

Dashboard opens at localhost:8503

## GitHub
https://github.com/Ayush240207/inventory-optimisation

## Project Structure
inventory-optimisation/
├── data/raw/retailer_template.xlsx
├── notebooks/
│   ├── 01_eda.ipynb
│   ├── 02_baseline.ipynb
│   ├── 04_forecasting.ipynb
│   └── 05_inventory.ipynb
├── app/dashboard.py
├── requirements.txt
└── PROJECT_BRIEF.md

## Three Dashboard Tabs
1. Performance Analysis — winners/losers, top 50 articles by sell through and margin
2. Inventory Status — days of cover, stock health per SKU
3. Order Recommendations — order quantities, working capital, priority levels

## Excel Template Format — 3 Sheets
Sheet 1 — Product_Master: Style_No, Article_No, Product_Name, Category, Color, Gender, Cost_Price, MRP, Lead_Time_Days, MOQ
Sheet 2 — Sales_History: Style_No, Date_of_Purchase, Date_of_Sale, Units_Bought, Units_Sold, Selling_Price
Sheet 3 — Current_Inventory: Style_No, Units_On_Hand, Units_On_Order, Expected_Delivery_Date

## Key Calculations
Daily Velocity = Total Units Sold / Selling Days
Days of Cover = Units on Hand / Daily Velocity
Safety Stock = 1.65 x std_daily_sales x sqrt(lead_time)
Reorder Point = (Daily Velocity x Lead Time) + Safety Stock
Order Qty = max(MOQ, Forecast_30_days + Safety_Stock - Current_Stock)
Working Capital = Order Qty x Cost Price

## ML Work Done
1. Manual gradient descent on AP-1001 — educational, understood internals
2. Sklearn linear regression at brand level — FlexDenim MAE 24 units/month
3. Prophet time series on CasualCo — failed, predicted near zero
4. Simple average — beat Prophet 3x, MAE 3.9 units/day
Key finding: simpler models outperformed complex ones with limited data

## Tech Stack
Python 3.11, Pandas, NumPy, Scikit-learn, Prophet, Streamlit, Matplotlib, Git

## Current Status
- Dashboard built and running with dropdown driven UI
- Theme toggle (light/dark) implemented
- Deployed on GitHub
- Next task: improve UI/UX

## Known Issues to Fix
- Single transaction SKUs produce unrealistic velocity
- Order qty occasionally lower than reorder point (partially fixed)
- Safety stock double counted in some scenarios

## Environment Setup
conda create -n inventory-project python=3.11
conda activate inventory-project
pip install pandas numpy matplotlib seaborn scikit-learn openpyxl statsmodels prophet streamlit jupyter
