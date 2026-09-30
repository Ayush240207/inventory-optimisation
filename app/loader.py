import re
import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

def norm(s):
    return re.sub(r"[^a-z0-9]", "", str(s).lower())

ALIASES = {
    "Style_No": ["styleno","style","stylecode","sku","skucode","itemcode","productcode","articleno","article","code","itemno"],
    "Product_Name": ["productname","product","name","itemname","description","item"],
    "Category": ["category","subcategory","type","producttype","dept","department"],
    "Color": ["color","colour","shade"],
    "Gender": ["gender","sex","segment"],
    "Cost_Price": ["costprice","cost","cp","purchaseprice","buyprice","unitcost"],
    "MRP": ["mrp","retailprice","listprice","price","maxretailprice"],
    "Lead_Time_Days": ["leadtimedays","leadtime","deliverydays","lt"],
    "MOQ": ["moq","minorderqty","minimumorderquantity","minqty"],
    "Date_of_Sale": ["dateofsale","saledate","date","invoicedate","billdate","transactiondate","solddate"],
    "Date_of_Purchase": ["dateofpurchase","purchasedate","grndate","receiveddate","buydate"],
    "Units_Bought": ["unitsbought","qtybought","purchasedqty","totalunitsbought","qtypurchased","receivedqty"],
    "Units_Sold": ["unitssold","qtysold","quantity","qty","totalsold","soldqty","units"],
    "Selling_Price": ["sellingprice","saleprice","finalsaleprice","netprice","sp","finalprice"],
    "Units_On_Hand": ["unitsonhand","onhand","stock","stockonhand","currentstock","closingstock","inventory","soh"],
    "Units_On_Order": ["unitsonorder","onorder","intransit","intransitqty","pendingorder"],
    "Expected_Delivery_Date": ["expecteddeliverydate","deliverydate","eta","expecteddate"],
}

def standardise(df, fields, notes, label):
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    used, rename = set(), {}
    for target in fields:
        for alias in ALIASES[target]:
            match = [c for c in df.columns if norm(c) == alias and c not in used]
            if match:
                rename[match[0]] = target
                used.add(match[0])
                if match[0] != target:
                    notes.append(f"{label}: using '{match[0]}' as {target}")
                break
    return df.rename(columns=rename)
def has_any(df, target):
    return bool({norm(c) for c in df.columns} & set(ALIASES[target]))

def pick_sheets(sheets, notes):
    names = list(sheets)
    byname = {norm(n): n for n in names}
    sales = byname.get("saleshistory") or byname.get("sales")
    prod = byname.get("productmaster") or byname.get("products")
    inv = byname.get("currentinventory") or byname.get("inventory") or byname.get("stock")
    for n in names:
        df = sheets[n]
        if not sales and has_any(df, "Date_of_Sale") and has_any(df, "Units_Sold"):
            sales = n
        elif not inv and has_any(df, "Units_On_Hand") and n != sales:
            inv = n
    if not sales:
        raise ValueError("Couldn't find sales data. Need a sheet with a sale date and units sold.")
    if not prod:
        prod = next((n for n in names if n not in (sales, inv)), sales)
    notes.append(f"Sheets used: products '{prod}', sales '{sales}', inventory '{inv or 'none'}'")
    return prod, sales, inv

PROD_F = ["Style_No","Product_Name","Category","Color","Gender","Cost_Price","MRP","Lead_Time_Days","MOQ"]
SALES_F = ["Style_No","Date_of_Sale","Date_of_Purchase","Units_Bought","Units_Sold","Selling_Price","Cost_Price","MRP","Product_Name","Category","Color","Gender"]
INV_F = ["Style_No","Units_On_Hand","Units_On_Order","Expected_Delivery_Date"]

def num(df, col, default=0):
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(default)
@st.cache_data(show_spinner="Reading your file...")
def load_data_from_bytes(file_bytes, filename):
    notes = []
    if filename.lower().endswith(".csv"):
        sheets = {"Sheet1": pd.read_csv(BytesIO(file_bytes))}
    else:
        sheets = pd.read_excel(BytesIO(file_bytes), sheet_name=None)
    sheets = {n: d.dropna(how="all") for n, d in sheets.items()}
    p_name, s_name, i_name = pick_sheets(sheets, notes)

    sales = standardise(sheets[s_name], SALES_F, notes, "Sales")
    products = standardise(sheets[p_name], PROD_F, notes, "Products")
    if "Style_No" not in sales.columns:
        raise ValueError("Couldn't find a product code column (e.g. Style_No, SKU, Item Code) in your sales data.")
    if "Style_No" not in products.columns:
        products = sales.copy()
        notes.append("No product sheet matched, so product details were taken from sales data.")
    for df in (sales, products):
        df["Style_No"] = df["Style_No"].astype(str).str.strip()
    products = products.drop_duplicates("Style_No")
    for col in ["Product_Name","Category","Color","Gender","Cost_Price","MRP"]:
        if col not in products.columns and col in sales.columns:
            products = products.merge(sales.groupby("Style_No")[col].first().reset_index(), on="Style_No", how="left")
    if "Selling_Price" not in sales.columns:
        if "MRP" in products.columns:
            sales = sales.merge(products[["Style_No","MRP"]].rename(columns={"MRP":"Selling_Price"}), on="Style_No", how="left")
            notes.append("No selling price found, so MRP is used instead.")
        else:
            raise ValueError("Need at least a selling price or MRP column.")
    num(sales, "Selling_Price")
    if "Product_Name" not in products.columns:
        products["Product_Name"] = products["Style_No"]
    if "Category" not in products.columns:
        products["Category"] = "Uncategorised"
        notes.append("No category column, so all products are grouped as 'Uncategorised'.")
    for col in ["Color","Gender","Lead_Time_Days","MOQ"]:
        if col not in products.columns:
            products[col] = np.nan
    top_sp = sales.groupby("Style_No")["Selling_Price"].max()
    if "MRP" not in products.columns:
        products["MRP"] = products["Style_No"].map(top_sp)
        notes.append("No MRP found, so the highest selling price is used.")
    num(products, "MRP")
    if "Cost_Price" not in products.columns:
        products["Cost_Price"] = products["MRP"] * 0.5
        notes.append("⚠️ No cost price found, so it's assumed to be 50% of MRP. Margins are estimates.")
    num(products, "Cost_Price")
    for col in ["Lead_Time_Days","MOQ"]:
        products[col] = pd.to_numeric(products[col], errors="coerce")
    if "Units_Sold" not in sales.columns:
        raise ValueError("Couldn't find units sold (e.g. Units_Sold, Qty, Quantity) in your sales data.")
    num(sales, "Units_Sold")
    if "Units_Bought" not in sales.columns:
        sales["Units_Bought"] = sales["Units_Sold"]
        notes.append("⚠️ No units bought column, so sell-through will show 100%.")
    num(sales, "Units_Bought")
    if "Date_of_Sale" not in sales.columns:
        raise ValueError("Couldn't find a sale date column (e.g. Date, Sale Date, Invoice Date).")
    sales["Date_of_Sale"] = pd.to_datetime(sales["Date_of_Sale"], errors="coerce", dayfirst=True)
    if "Date_of_Purchase" not in sales.columns:
        sales["Date_of_Purchase"] = sales["Date_of_Sale"]
    sales["Date_of_Purchase"] = pd.to_datetime(sales["Date_of_Purchase"], errors="coerce", dayfirst=True)
    bad = int(sales["Date_of_Sale"].isna().sum())
    if bad:
        notes.append(f"Skipped {bad} rows with unreadable dates.")
    sales = sales.dropna(subset=["Date_of_Sale"])
    sales = sales[["Style_No","Date_of_Sale","Date_of_Purchase","Units_Bought","Units_Sold","Selling_Price"]]
    if i_name:
        inventory = standardise(sheets[i_name], INV_F, notes, "Inventory")
    else:
        inventory = pd.DataFrame({"Style_No": products["Style_No"]})
    if "Style_No" not in inventory.columns:
        inventory = pd.DataFrame({"Style_No": products["Style_No"]})
    inventory["Style_No"] = inventory["Style_No"].astype(str).str.strip()
    if "Units_On_Hand" not in inventory.columns:
        est = sales.groupby("Style_No")[["Units_Bought","Units_Sold"]].sum()
        inventory["Units_On_Hand"] = inventory["Style_No"].map(est["Units_Bought"] - est["Units_Sold"]).clip(lower=0)
        notes.append("⚠️ No current stock found, so it's estimated as units bought minus units sold.")
    num(inventory, "Units_On_Hand")
    if "Units_On_Order" not in inventory.columns:
        inventory["Units_On_Order"] = 0
    num(inventory, "Units_On_Order")
    if "Expected_Delivery_Date" not in inventory.columns:
        inventory["Expected_Delivery_Date"] = ""
    inventory = inventory.drop_duplicates("Style_No")
    return products, sales, inventory, notes

def load_data(uploaded_file):
    products, sales, inventory, notes = load_data_from_bytes(uploaded_file.getvalue(), uploaded_file.name)
    if notes:
        with st.expander(f"ℹ️ How we read your file ({len(notes)} notes)"):
            for n in notes:
                st.write("• " + n)
    return products, sales, inventory
