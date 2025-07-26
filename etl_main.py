import pandas as pd
from sqlalchemy import create_engine
from etl.data_cleaner import clean_sales, clean_customers
from etl.config import DB_CONFIG
from urllib.parse import quote_plus
import os

def connect_to_db():
    encoded_password = quote_plus(DB_CONFIG['password'])
    conn_str = f"mssql+pyodbc://{DB_CONFIG['username']}:{encoded_password}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}?driver={DB_CONFIG['driver']}"
    return create_engine(conn_str)

def main():
    try:
        # Load the combined dataset
        csv_path = os.path.join(os.path.dirname(__file__), 'retail_combined.csv')
        df = pd.read_csv(csv_path, encoding="latin1")

        print("CSV columns:", df.columns.tolist())

        # Separate into sales and customer DataFrames
        sales_df = df[['Row ID', 'Order ID', 'Order Date', 'Ship Date', 'Customer ID', 'Category', 'Sales', 'Quantity', 'Discount', 'Profit']]
        cust_df = df[['Customer ID', 'Customer Name', 'Segment']].drop_duplicates()

        # Clean the data
        sales_df = clean_sales(sales_df if isinstance(sales_df, pd.DataFrame) else pd.DataFrame())
        cust_df = clean_customers(cust_df if isinstance(cust_df, pd.DataFrame) else pd.DataFrame())

        # Connect and upload
        engine = connect_to_db()
        sales_df.to_sql('sales_cleaned', con=engine, if_exists='replace', index=False)
        cust_df.to_sql('customers_cleaned', con=engine, if_exists='replace', index=False)

        print("✅ ETL process completed and data loaded into SQL Server.")
    except Exception as e:
        print(f"❌ ETL process failed: {e}")

if __name__ == "__main__":
    main()