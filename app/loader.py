import re
import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

def norm(s):
    return re.sub(r"[^a-z0-9]", "", str(s).lower())

def norm_keys(s):
    """Both the full name and the name without bracketed units,
    e.g. 'MRP (INR)' -> {'mrpinr', 'mrp'}."""
    return {norm(s), norm(re.sub(r"\(.*?\)", "", str(s)))}

ALIASES = {
    "Style_No": ["styleno","sku","skucode","skuid","itemcode","productcode","articleno","article","code","itemno","style","stylecode"],
    "Product_Name": ["productname","product","name","itemname","description","item"],
    "Category": ["category","subcategory","type","producttype","dept","department"],
    "Color": ["color","colour","shade"],
    "Gender": ["gender","sex","segment","gendercategory"],
    "Cost_Price": ["costprice","cost","cp","purchaseprice","buyprice","unitcost"],
    "MRP": ["mrp","retailprice","listprice","price","maxretailprice"],
    "Lead_Time_Days": ["leadtimedays","leadtime","deliverydays","lt","lead","deliverytime"],
    "MOQ": ["moq","minorderqty","minimumorderquantity","minqty"],
    "Date_of_Sale": ["dateofsale","saledate","date","invoicedate","billdate","transactiondate","solddate"],
    "Date_of_Purchase": ["dateofpurchase","purchasedate","grndate","receiveddate","buydate"],
    "Units_Bought": ["unitsbought","qtybought","purchasedqty","totalunitsbought","qtypurchased","receivedqty"],
    "Units_Sold": ["unitssold","qtysold","quantity","qty","totalsold","soldqty","units"],
    "Selling_Price": ["sellingprice","saleprice","finalsaleprice","netprice","sp","finalprice"],
    "Units_On_Hand": ["unitsonhand","onhand","stockonhand","currentstock","closingstock","stock","inventory","soh"],
    "Units_On_Order": ["unitsonorder","onorder","intransit","intransitqty","pendingorder"],
    "Expected_Delivery_Date": ["expecteddeliverydate","deliverydate","eta","expecteddate","intransitexpecteddate"],
}

def standardise(df, fields, notes, label):
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    used, rename = set(), {}
    for target in fields:
        for alias in ALIASES[target]:
            match = [c for c in df.columns if norm(c) == alias and c not in used]
            if not match:
                match = [c for c in df.columns if alias in norm_keys(c) and c not in used]
            if match:
                rename[match[0]] = target
                used.add(match[0])
                if match[0] != target:
                    notes.append(f"{label}: using '{match[0]}' as {target}")
                break
    return df.rename(columns=rename)
def has_any(df, target):
    keys = set().union(*[norm_keys(c) for c in df.columns]) if len(df.columns) else set()
    return bool(keys & set(ALIASES[target]))

ALL_ALIASES = {a for v in ALIASES.values() for a in v}

def fix_header(raw):
    """Many exports have a title or notes above the real column names.
    Use the first row (in the top 20) that looks like a header."""
    best, best_hits = None, 1
    for i in range(min(20, len(raw))):
        cells = [c for c in raw.iloc[i].tolist() if pd.notna(c)]
        hits = sum(1 for c in cells if norm_keys(c) & ALL_ALIASES)
        if hits > best_hits:
            best, best_hits = i, hits
            if hits >= 3:
                break
    if best is None:
        return None
    df = raw.iloc[best + 1:].copy()
    cols, seen = [], {}
    for j, c in enumerate(raw.iloc[best].tolist()):
        name = str(c).strip() if pd.notna(c) else f"Unnamed_{j}"
        if name in seen:
            seen[name] += 1
            name = f"{name}_{seen[name]}"
        else:
            seen[name] = 0
        cols.append(name)
    df.columns = cols
    return df.dropna(how="all").reset_index(drop=True)

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

ISO_DATE = re.compile(r"^\s*\d{4}[-/.]\d{1,2}[-/.]\d{1,2}")

def parse_dates(col):
    """Read dates safely. Real Excel dates are kept as they are. Text dates that
    start with the year (2026-02-01) are read year-month-day; other text dates
    (01/02/2026) are read day-first, as is usual in India and the UK.
    The old code read everything day-first, which turned 2026-02-01 into 2 Jan."""
    col = pd.Series(col)
    out = pd.Series(pd.NaT, index=col.index, dtype="datetime64[ns]")
    is_dt = col.apply(lambda v: isinstance(v, (pd.Timestamp, np.datetime64)) or hasattr(v, "year"))
    if is_dt.any():
        out[is_dt] = pd.to_datetime(col[is_dt], errors="coerce")
    nums = pd.to_numeric(col.where(~is_dt), errors="coerce")
    serial = nums.between(20000, 80000)  # Excel day numbers (1954–2119)
    if serial.any():
        out[serial] = pd.to_datetime(nums[serial], unit="D", origin="1899-12-30")
    text = col[~is_dt & ~serial & col.notna()].astype(str)
    iso = text.str.match(ISO_DATE)
    if iso.any():
        out[iso[iso].index] = pd.to_datetime(text[iso], errors="coerce", yearfirst=True, format="mixed")
    other = text[~iso]
    if len(other):
        out[other.index] = pd.to_datetime(other, errors="coerce", dayfirst=True, format="mixed")
    return out

def num(df, col, default=0):
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(default)
@st.cache_data(show_spinner="Reading your file...")
def load_data_from_bytes(file_bytes, filename):
    notes = []
    if filename.lower().endswith(".csv"):
        raw_sheets = {"Sheet1": pd.read_csv(BytesIO(file_bytes), header=None)}
    else:
        raw_sheets = pd.read_excel(BytesIO(file_bytes), sheet_name=None, header=None)
    sheets = {}
    for n, raw in raw_sheets.items():
        df = fix_header(raw.dropna(how="all").reset_index(drop=True))
        if df is not None:
            sheets[n] = df
    if not sheets:
        raise ValueError("Couldn't find any column headers we recognise. Download the template for a working example.")
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
    sales["Date_of_Sale"] = parse_dates(sales["Date_of_Sale"])
    if "Date_of_Purchase" not in sales.columns:
        sales["Date_of_Purchase"] = sales["Date_of_Sale"]
    sales["Date_of_Purchase"] = parse_dates(sales["Date_of_Purchase"])
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
        inventory["Expected_Delivery_Date"] = pd.NaT
    inventory["Expected_Delivery_Date"] = parse_dates(inventory["Expected_Delivery_Date"])
    missing_inv = set(sales["Style_No"]) - set(inventory["Style_No"])
    if missing_inv and i_name:
        notes.append(f"⚠️ {len(missing_inv)} products have sales but no row in the stock sheet, so their stock is taken as 0.")
    inventory = inventory.drop_duplicates("Style_No")
    return products, sales, inventory, notes

def load_data(uploaded_file):
    products, sales, inventory, notes = load_data_from_bytes(uploaded_file.getvalue(), uploaded_file.name)
    if notes:
        with st.expander(f"ℹ️ How we read your file ({len(notes)} notes)"):
            for n in notes:
                st.write("• " + n)
    return products, sales, inventory
