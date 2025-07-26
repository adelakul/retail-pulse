from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
import pyodbc

# Connection parameters for local test
host = "host.docker.internal,14330"  # or "127.0.0.1"
port = "1433"       # Default SQL Server port
database = "master"
username = "sa"
password = "MyNewP@ssw0rd123"
driver = "ODBC Driver 17 for SQL Server"

# Encode password for special characters
encoded_password = quote_plus(password)

# Create connection string
conn_str = f"mssql+pyodbc://{username}:{encoded_password}@{host}:{port}/{database}?driver={driver}"

try:
    # Create engine
    engine = create_engine(conn_str)
    
    # Test the connection
    with engine.connect() as conn:
        result = conn.execute(text("SELECT GETDATE()"))
        for row in result:
            print("✅ SQL Server time:", row[0])
except Exception as e:
    print(f"❌ Connection failed: {str(e)}")