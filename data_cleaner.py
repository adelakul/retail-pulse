# etl/data_cleaner.py
import pandas as pd

print("DEBUG: Running data_cleaner.py version with Order Date and Ship Date columns.")

def clean_sales(df: pd.DataFrame) -> pd.DataFrame:
    # Convert date columns to datetime
    df.loc[:, 'Order Date'] = pd.to_datetime(df['Order Date'], errors='coerce')
    df.loc[:, 'Ship Date'] = pd.to_datetime(df['Ship Date'], errors='coerce')

    # Remove rows with missing or invalid dates
    df = df.dropna(subset=['Order Date'])

    # Ensure numeric columns are correct
    numeric_cols = ['Sales', 'Quantity', 'Discount', 'Profit']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        df[col] = df[col].fillna(0)
    df['Quantity'] = df['Quantity'].astype(int)
    df['Sales'] = df['Sales'].astype(float)
    df['Discount'] = df['Discount'].astype(float)
    df['Profit'] = df['Profit'].astype(float)

    # Derive Price per Unit if not present
    df['Price per Unit'] = df['Sales'] / df['Quantity'].replace(0, 1)  # Avoid division by zero

    # Drop duplicates based on Row ID or Order ID
    df = df.drop_duplicates(subset='Row ID')

    return df

def clean_customers(df: pd.DataFrame) -> pd.DataFrame:
    # Drop duplicates based on Customer ID
    df = df.drop_duplicates(subset='Customer ID')

    # Standardize Segment values (if present)
    if 'Segment' in df.columns:
        df['Segment'] = df['Segment'].astype(str).str.strip().str.title()

    # Ensure Age is numeric and reasonable (if present)
    if 'Age' in df.columns:
        df['Age'] = pd.to_numeric(df['Age'], errors='coerce')
        mask = df['Age'].between(10, 100)
        df = df.loc[mask].copy()

    return df