#!/usr/bin/env python3
"""
Local ETL Runner - Run the ETL process directly on the host machine
"""

import sys
import os

# Add the current directory to Python path so we can import etl modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the ETL process
from etl.etl_main import main

if __name__ == "__main__":
    print("🚀 Starting ETL process locally...")
    main() 