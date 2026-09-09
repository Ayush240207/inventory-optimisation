# Retail Inventory Optimiser

A universal inventory optimisation tool for small retail businesses. Upload your sales data and instantly get recommendations on what to order, how much, and how urgently.

## What It Does

- **Performance Analysis** — identify winners and losers, top 50 articles by sell through and margin
- **Inventory Status** — live stock status showing days of cover for every product
- **Order Recommendations** — exact order quantities with working capital estimates and what-if scenarios

## How To Run

```bash
conda activate inventory-project
cd inventory-optimisation
streamlit run app/dashboard.py
```

Dashboard opens at localhost:8501

## Excel Template Format

Upload a file with three sheets:

**Sheet 1 — Product_Master**
Style_No, Article_No, Product_Name, Category, Color, Gender, Cost_Price, MRP, Lead_Time_Days, MOQ

**Sheet 2 — Sales_History**
Style_No, Date_of_Purchase, Date_of_Sale, Units_Bought, Units_Sold, Selling_Price

**Sheet 3 — Current_Inventory**
Style_No, Units_On_Hand, Units_On_Order, Expected_Delivery_Date

## Tech Stack
- Python 3.11
- Pandas, NumPy
- Scikit-learn
- Prophet
- Streamlit
- Matplotlib

## Setup

```bash
conda create -n inventory-project python=3.11
conda activate inventory-project
pip install pandas numpy matplotlib seaborn scikit-learn openpyxl statsmodels prophet streamlit jupyter
```

## Project Background

Built alongside Andrew Ng's ML Specialization. The project explores demand forecasting using linear regression, Prophet time series modelling, and formula-based inventory calculations. Key finding: simple models often outperform complex ones with limited data.

## Author
UMass Amherst — Sophomore
