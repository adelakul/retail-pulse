import os

# Check if running in Docker container
IS_DOCKER = os.path.exists('/.dockerenv')

if IS_DOCKER:
    # Docker configuration - use host IP
    DB_CONFIG = {
        "username": "sa",
        "password": "MyNewP@ssw0rd123",
        "host": "192.168.1.96",  # Updated Host IP address for Docker
        "port": "14330",  # SQL Server port
        "database": "retail_2025",
        "driver": "ODBC Driver 17 for SQL Server"
    }
else:
    # Local configuration
    DB_CONFIG = {
        "username": "sa",
        "password": "MyNewP@ssw0rd123",
        "host": "localhost",  # Use localhost for local execution
        "port": "14330",  # SQL Server port
        "database": "retail_2025",
        "driver": "ODBC Driver 17 for SQL Server"
    }
