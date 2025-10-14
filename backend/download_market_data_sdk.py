#!/usr/bin/env python3
"""
Market Data Download Script using Alpaca SDK
This script uses the official Alpaca Python SDK to download complete minute-by-minute data
and store it in our database.
"""

import pandas as pd
import sqlite3
from datetime import datetime, timezone
from alpaca.data import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from config import ALPACA_KEY, ALPACA_SECRET

# Database path
DB_PATH = 'market_data.db'

def init_database():
    """Initialize the market data database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS market_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            timestamp INTEGER NOT NULL,
            open REAL NOT NULL,
            high REAL NOT NULL,
            low REAL NOT NULL,
            close REAL NOT NULL,
            volume INTEGER NOT NULL,
            UNIQUE(symbol, timestamp)
        )
    ''')
    
    # Create indexes for better performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_symbol_timestamp ON market_data(symbol, timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON market_data(timestamp)')
    
    conn.commit()
    conn.close()

def download_and_store_market_data(symbol, date):
    """Download market data for a specific symbol and date using Alpaca SDK"""
    
    print(f"📡 Downloading {symbol} market data for {date}")
    
    try:
        # Initialize the Alpaca data client
        client = StockHistoricalDataClient(ALPACA_KEY, ALPACA_SECRET)
        
        # Convert date to timezone-aware timestamps
        start_date = pd.Timestamp(f'{date} 09:30:00', tz='America/New_York')
        end_date = pd.Timestamp(f'{date} 16:00:00', tz='America/New_York')
        
        print(f"   🕐 Start: {start_date} (ET)")
        print(f"   🕐 End: {end_date} (ET)")
        
        # Create a request for minute-level bars
        request_params = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=TimeFrame.Minute,
            start=start_date,
            end=end_date
        )
        
        # Fetch the data
        bars = client.get_stock_bars(request_params)
        df = bars.df
        
        print(f"   📈 Data points received: {len(df)}")
        
        if len(df) == 0:
            print(f"   ❌ No data received for {symbol} on {date}")
            return 0
        
        # Store data in database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        stored_count = 0
        skipped_count = 0
        
        for (symbol_name, timestamp), row in df.iterrows():
            try:
                # Convert timestamp to Unix timestamp
                unix_timestamp = int(timestamp.timestamp())
                
                cursor.execute('''
                    INSERT OR REPLACE INTO market_data 
                    (symbol, timestamp, open, high, low, close, volume)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    symbol_name,
                    unix_timestamp,
                    float(row['open']),
                    float(row['high']),
                    float(row['low']),
                    float(row['close']),
                    int(row['volume'])
                ))
                stored_count += 1
                
            except Exception as e:
                print(f"   ⚠️  Error storing data point: {e}")
                skipped_count += 1
        
        conn.commit()
        conn.close()
        
        print(f"   ✅ Stored {stored_count} data points")
        if skipped_count > 0:
            print(f"   ⚠️  Skipped {skipped_count} data points due to errors")
        
        return stored_count
        
    except Exception as e:
        print(f"   💥 Error downloading {symbol} data: {e}")
        return 0

def download_all_symbols_for_date(date):
    """Download market data for all symbols on a specific date"""
    
    symbols = ['AAPL', 'AMZN', 'AVGO', 'GOOGL', 'META', 'MSFT', 'NFLX', 'NVDA', 'PLTR', 'TSLA']
    
    print(f"🚀 Downloading market data for all symbols on {date}")
    print("=" * 60)
    
    total_stored = 0
    
    for symbol in symbols:
        stored = download_and_store_market_data(symbol, date)
        total_stored += stored
        print()  # Empty line for readability
    
    print("=" * 60)
    print(f"✅ Download completed! Total data points stored: {total_stored}")
    print("=" * 60)

def verify_database_data(date):
    """Verify the data stored in the database for a specific date"""
    
    print(f"🔍 Verifying database data for {date}")
    print("-" * 40)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get data counts by symbol for the date
    cursor.execute('''
        SELECT symbol, COUNT(*) as count, 
               MIN(timestamp) as first_timestamp,
               MAX(timestamp) as last_timestamp
        FROM market_data 
        WHERE date(datetime(timestamp, 'unixepoch')) = ?
        GROUP BY symbol
        ORDER BY count DESC
    ''', (date,))
    
    results = cursor.fetchall()
    
    if results:
        print(f"📊 Data points by symbol on {date}:")
        for symbol, count, first_ts, last_ts in results:
            first_time = datetime.fromtimestamp(first_ts, tz=timezone.utc).strftime('%H:%M:%S UTC')
            last_time = datetime.fromtimestamp(last_ts, tz=timezone.utc).strftime('%H:%M:%S UTC')
            print(f"   {symbol}: {count} points ({first_time} - {last_time})")
    else:
        print(f"❌ No data found for {date}")
    
    conn.close()

def main():
    """Main function"""
    
    print("🏁 Starting Market Data Download using Alpaca SDK")
    print("=" * 80)
    
    # Initialize database
    init_database()
    print("✅ Database initialized")
    
    # Download data for specific dates
    dates = ['2025-10-13', '2025-10-14']
    
    for date in dates:
        print(f"\n📅 Processing date: {date}")
        download_all_symbols_for_date(date)
        verify_database_data(date)
        print()
    
    print("🎉 All downloads completed!")

if __name__ == "__main__":
    main()
