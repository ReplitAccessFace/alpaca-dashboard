#!/usr/bin/env python3
"""
Simple script to download 1-minute market data from Alpaca for NASDAQ trading hours
"""

import requests
import sqlite3
from datetime import datetime, timedelta
import json

# Alpaca Market Data API Configuration
API_KEY = "PKBGXR1F3WTXQVP2JCBG"
API_SECRET = "pvQhlQnZruLMGgl0jptEWawqCaanPQGkIGsHmOiu"
BASE_URL = "https://data.alpaca.markets/v2"

def download_stock_data(symbol, start_date, end_date=None):
    """Download 1-minute bars for a stock during NASDAQ trading hours"""
    
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    
    print(f"Downloading {symbol} data from {start_date} to {end_date}")
    
    # NASDAQ trading hours: 9:30 AM - 4:00 PM ET = 1:30 PM - 8:00 PM UTC
    start_time = f"{start_date}T13:30:00Z"  # 9:30 AM ET
    end_time = f"{end_date}T20:00:00Z"      # 4:00 PM ET
    
    url = f"{BASE_URL}/stocks/{symbol}/bars"
    headers = {
        "APCA-API-KEY-ID": API_KEY,
        "APCA-API-SECRET-KEY": API_SECRET
    }
    
    params = {
        "start": start_time,
        "end": end_time,
        "timeframe": "1Min",
        "limit": 1000,
        "feed": "iex"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        if "bars" in data and data["bars"]:
            bars = data["bars"]
            print(f"Downloaded {len(bars)} 1-minute bars for {symbol}")
            return bars
        else:
            print(f"No data found for {symbol}")
            return []
            
    except Exception as e:
        print(f"Error downloading {symbol}: {e}")
        return []

def save_to_database(symbol, bars):
    """Save bars to SQLite database"""
    
    conn = sqlite3.connect('market_data.db')
    cursor = conn.cursor()
    
    # Create table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS market_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            timestamp INTEGER,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert data
    for bar in bars:
        timestamp = int(datetime.fromisoformat(bar["t"].replace("Z", "+00:00")).timestamp())
        cursor.execute('''
            INSERT OR REPLACE INTO market_data 
            (symbol, timestamp, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            symbol,
            timestamp,
            float(bar["o"]),
            float(bar["h"]),
            float(bar["l"]),
            float(bar["c"]),
            int(bar["v"])
        ))
    
    conn.commit()
    conn.close()
    print(f"Saved {len(bars)} bars for {symbol} to database")

def main():
    """Main function to download data for specified stocks"""
    
    # List of stocks to download
    symbols = ["AMZN", "AAPL", "GOOGL", "MSFT", "TSLA", "NVDA", "META", "NFLX", "PLTR", "AVGO"]
    
    # Download data for each day from October 6th to October 10th, 2025
    dates = ["2025-10-06", "2025-10-07", "2025-10-08", "2025-10-09", "2025-10-10"]
    
    print("Starting market data download...")
    print(f"Symbols: {', '.join(symbols)}")
    print(f"Dates: {', '.join(dates)}")
    print(f"Timeframe: 1-minute bars")
    print(f"Trading hours: 9:30 AM - 4:00 PM ET (NASDAQ hours)")
    print("-" * 50)
    
    for date in dates:
        print(f"\n=== Downloading data for {date} ===")
        for symbol in symbols:
            bars = download_stock_data(symbol, date, date)  # Same start and end date
            if bars:
                save_to_database(symbol, bars)
            print()
    
    print("Download complete!")

if __name__ == "__main__":
    main()
