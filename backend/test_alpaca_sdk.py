#!/usr/bin/env python3
"""
Alpaca SDK Market Data Test Script
This script uses the official Alpaca Python SDK to download minute-by-minute data
and verify what data is actually available.
"""

import pandas as pd
from datetime import datetime, timezone
from alpaca.data import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from config import ALPACA_KEY, ALPACA_SECRET

def test_alpaca_sdk():
    """Test using the official Alpaca Python SDK"""
    
    print("=" * 80)
    print("ALPACA SDK MARKET DATA TEST")
    print("=" * 80)
    
    # Initialize the Alpaca data client
    try:
        client = StockHistoricalDataClient(ALPACA_KEY, ALPACA_SECRET)
        print("✅ Alpaca client initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize Alpaca client: {e}")
        return
    
    # Test symbols and dates
    symbols = ['NFLX', 'TSLA', 'AAPL', 'PLTR']
    test_dates = ['2025-10-13', '2025-10-14']
    
    for date in test_dates:
        print(f"\n📅 Testing date: {date}")
        print("-" * 50)
        
        # Convert date to timezone-aware timestamps
        start_date = pd.Timestamp(f'{date} 09:30:00', tz='America/New_York')
        end_date = pd.Timestamp(f'{date} 16:00:00', tz='America/New_York')
        
        print(f"🕐 Start: {start_date} (ET)")
        print(f"🕐 End: {end_date} (ET)")
        
        for symbol in symbols:
            print(f"\n🔍 Testing {symbol} on {date}")
            
            try:
                # Create a request for minute-level bars
                request_params = StockBarsRequest(
                    symbol_or_symbols=symbol,
                    timeframe=TimeFrame.Minute,
                    start=start_date,
                    end=end_date
                )
                
                print(f"   📡 Fetching data...")
                
                # Fetch the data
                bars = client.get_stock_bars(request_params)
                
                # Convert to DataFrame
                df = bars.df
                
                print(f"   📈 Data points received: {len(df)}")
                
                if len(df) > 0:
                    # Show first few timestamps
                    print(f"   🕐 First 3 timestamps:")
                    for i, (timestamp, row) in enumerate(df.head(3).iterrows()):
                        print(f"      {i+1}. {timestamp}")
                    
                    # Show last few timestamps
                    print(f"   🕐 Last 3 timestamps:")
                    for i, (timestamp, row) in enumerate(df.tail(3).iterrows()):
                        print(f"      {len(df)-2+i}. {timestamp}")
                    
                    # Check for gaps
                    if len(df) > 1:
                        gaps = []
                        # Handle multi-index DataFrame (symbol, timestamp)
                        if isinstance(df.index, pd.MultiIndex):
                            timestamps = df.index.get_level_values(1)  # Get timestamp level
                        else:
                            timestamps = df.index
                        
                        for i in range(1, len(timestamps)):
                            prev_time = timestamps[i-1]
                            curr_time = timestamps[i]
                            gap_minutes = (curr_time - prev_time).total_seconds() / 60
                            
                            if gap_minutes > 1.5:  # More than 1.5 minutes gap
                                gaps.append({
                                    'from': prev_time,
                                    'to': curr_time,
                                    'gap_minutes': gap_minutes
                                })
                        
                        if gaps:
                            print(f"   ⚠️  Found {len(gaps)} gaps in data:")
                            for gap in gaps[:5]:  # Show first 5 gaps
                                print(f"      Gap: {gap['from']} → {gap['to']} ({gap['gap_minutes']:.1f} min)")
                            if len(gaps) > 5:
                                print(f"      ... and {len(gaps) - 5} more gaps")
                        else:
                            print(f"   ✅ No significant gaps found")
                    
                    # Show volume info
                    total_volume = df['volume'].sum()
                    avg_volume = df['volume'].mean()
                    print(f"   📊 Total volume: {total_volume:,}")
                    print(f"   📊 Average volume per minute: {avg_volume:,.0f}")
                    
                    # Show price range
                    high_price = df['high'].max()
                    low_price = df['low'].min()
                    print(f"   💰 Price range: ${low_price:.2f} - ${high_price:.2f}")
                    
                else:
                    print(f"   ❌ No data received")
                    
            except Exception as e:
                print(f"   💥 Exception: {e}")
            
            print()  # Empty line for readability
    
    print("=" * 80)
    print("TEST COMPLETED")
    print("=" * 80)

def test_specific_symbol_date(symbol, date):
    """Test a specific symbol and date with detailed output"""
    
    try:
        client = StockHistoricalDataClient(ALPACA_KEY, ALPACA_SECRET)
        
        start_date = pd.Timestamp(f'{date} 09:30:00', tz='America/New_York')
        end_date = pd.Timestamp(f'{date} 16:00:00', tz='America/New_York')
        
        print(f"🔍 Detailed test for {symbol} on {date}")
        print(f"🕐 Start: {start_date} (ET)")
        print(f"🕐 End: {end_date} (ET)")
        
        request_params = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=TimeFrame.Minute,
            start=start_date,
            end=end_date
        )
        
        bars = client.get_stock_bars(request_params)
        df = bars.df
        
        print(f"📊 Raw data shape: {df.shape}")
        print(f"📊 Columns: {list(df.columns)}")
        print(f"📊 Index type: {type(df.index)}")
        
        if len(df) > 0:
            print(f"\n📄 First 5 rows:")
            print(df.head())
            
            print(f"\n📄 Last 5 rows:")
            print(df.tail())
            
            # Save to CSV for inspection
            filename = f"{symbol}_{date}_minute_data.csv"
            df.to_csv(filename)
            print(f"\n💾 Data saved to: {filename}")
        
    except Exception as e:
        print(f"💥 Exception: {e}")

if __name__ == "__main__":
    print("Starting Alpaca SDK test...")
    
    # Run the main test
    test_alpaca_sdk()
    
    # Uncomment to test a specific symbol/date in detail
    # test_specific_symbol_date('NFLX', '2025-10-13')
