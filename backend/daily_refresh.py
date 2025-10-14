#!/usr/bin/env python3
"""
Daily refresh script for Alpaca Dashboard
This script automatically downloads today's market data and trades
Can be run manually or scheduled with cron
"""

import requests
import sys
from datetime import datetime

def refresh_today_data():
    """Call the backend API to refresh today's data"""
    try:
        print(f"[{datetime.now()}] Starting daily refresh...")
        
        # Call the refresh endpoint
        response = requests.post("http://localhost:8000/api/performance/refresh-today")
        
        if response.status_code == 200:
            result = response.json()
            print(f"[{datetime.now()}] ✅ Refresh successful!")
            print(f"  Date: {result['date']}")
            print(f"  Market Data: {result['market_data']['symbols_downloaded']}/{result['market_data']['total_symbols']} symbols")
            print(f"  Trades: {result['trades']['total_trades']} total, {result['trades']['new_trades_saved']} new")
            return True
        else:
            print(f"[{datetime.now()}] ❌ Refresh failed: {response.status_code}")
            print(f"  Error: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"[{datetime.now()}] ❌ Cannot connect to backend server. Is it running?")
        return False
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = refresh_today_data()
    sys.exit(0 if success else 1)