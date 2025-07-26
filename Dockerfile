FROM python:3.11

# Install system packages for SQL Server ODBC Driver
RUN apt-get update && apt-get install -y \
    curl \
    gnupg2 \
    apt-transport-https \
    unixodbc-dev \
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17

# Install Python libraries
RUN pip install pandas sqlalchemy pyodbc

# Set working directory
WORKDIR /workspace

# Copy ETL files
COPY etl/ /workspace/etl/

# Run ETL process instead of Jupyter
CMD ["python", "-m", "etl.etl_main"] 