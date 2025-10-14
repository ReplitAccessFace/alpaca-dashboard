#!/usr/bin/env python3
"""
Direct Alpaca Market API Test Script
This script directly accesses the Alpaca Market API to download minute-by-minute data
and verify what data is actually available.
"""

import requests
import json
from datetime import datetime, timedelta
from config import ALPACA_KEY, ALPACA_SECRET, ALPACA_BASE_URL

def test_alpaca_market_api():
    """Test direct access to Alpaca Market API"""
    
    # Test symbols
    symbols = ['NFLX', 'TSLA', 'AAPL', 'PLTR']
    
    # Test dates
    test_dates = ['2025-10-13', '2025-10-14']
    
    headers = {
        "APCA-API-KEY-ID": ALPACA_KEY,
        "APCA-API-SECRET-KEY": ALPACA_SECRET
    }
    
    print("=" * 80)
    print("ALPACA MARKET API DIRECT TEST")
    print("=" * 80)
    
    for date in test_dates:
        print(f"\n📅 Testing date: {date}")
        print("-" * 50)
        
        for symbol in symbols:
            print(f"\n🔍 Testing {symbol} on {date}")
            
            # API endpoint
            url = f"{ALPACA_BASE_URL}/stocks/{symbol}/bars"
            
            # Parameters for 1-minute data
            params = {
                "start": f"{date}T13:30:00Z",  # 9:30 AM ET = 1:30 PM UTC (market open)
                "end": f"{date}T20:00:00Z",    # 4:00 PM ET = 8:00 PM UTC (market close)
                "timeframe": "1Min",           # 1-minute candles
                "limit": 1000,                 # Max 1000 bars per request
                "feed": "iex"                  # Specify feed
            }
            
            try:
                print(f"   📡 Making API request...")
                print(f"   🔗 URL: {url}")
                print(f"   📋 Params: {params}")
                
                response = requests.get(url, headers=headers, params=params)
                
                print(f"   📊 Response Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Handle different response structures
                    if "bars" in data and isinstance(data["bars"], dict):
                        bars = data["bars"].get(symbol, [])
                    elif "bars" in data and isinstance(data["bars"], list):
                        bars = data["bars"]
                    else:
                        bars = []
                        print(f"   ⚠️  Unexpected response structure: {data}")
                    
                    print(f"   📈 Data points received: {len(bars)}")
                    
                    if bars:
                        # Show first few timestamps
                        print(f"   🕐 First 3 timestamps:")
                        for i, bar in enumerate(bars[:3]):
                            timestamp = bar["t"]
                            print(f"      {i+1}. {timestamp}")
                        
                        # Show last few timestamps
                        print(f"   🕐 Last 3 timestamps:")
                        for i, bar in enumerate(bars[-3:]):
                            timestamp = bar["t"]
                            print(f"      {len(bars)-2+i}. {timestamp}")
                        
                        # Check for gaps
                        if len(bars) > 1:
                            gaps = []
                            for i in range(1, len(bars)):
                                prev_time = datetime.fromisoformat(bars[i-1]["t"].replace("Z", "+00:00"))
                                curr_time = datetime.fromisoformat(bars[i]["t"].replace("Z", "+00:00"))
                                gap_minutes = (curr_time - prev_time).total_seconds() / 60
                                
                                if gap_minutes > 1.5:  # More than 1.5 minutes gap
                                    gaps.append({
                                        'from': bars[i-1]["t"],
                                        'to': bars[i]["t"],
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
                        total_volume = sum(bar["v"] for bar in bars)
                        avg_volume = total_volume / len(bars) if bars else 0
                        print(f"   📊 Total volume: {total_volume:,}")
                        print(f"   📊 Average volume per minute: {avg_volume:,.0f}")
                        
                    else:
                        print(f"   ❌ No data received")
                        
                else:
                    print(f"   ❌ API Error: {response.status_code}")
                    print(f"   📄 Response: {response.text}")
                    
            except Exception as e:
                print(f"   💥 Exception: {e}")
            
            print()  # Empty line for readability
    
    print("=" * 80)
    print("TEST COMPLETED")
    print("=" * 80)

def test_specific_symbol_date(symbol, date):
    """Test a specific symbol and date with detailed output"""
    
    headers = {
        "APCA-API-KEY-ID": ALPACA_KEY,
        "APCA-API-SECRET-KEY": ALPACA_SECRET
    }
    
    url = f"{ALPACA_BASE_URL}/stocks/{symbol}/bars"
    params = {
        "start": f"{date}T13:30:00Z",
        "end": f"{date}T20:00:00Z",
        "timeframe": "1Min",
        "limit": 1000,
        "feed": "iex"
    }
    
    print(f"🔍 Detailed test for {symbol} on {date}")
    print(f"📡 URL: {url}")
    print(f"📋 Params: {json.dumps(params, indent=2)}")
    
    try:
        response = requests.get(url, headers=headers, params=params)
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📄 Raw response: {json.dumps(data, indent=2)}")
        else:
            print(f"❌ Error response: {response.text}")
            
    except Exception as e:
        print(f"💥 Exception: {e}")

if __name__ == "__main__":
    print("Starting Alpaca Market API test...")
    
    # Run the main test
    test_alpaca_market_api()
    
    # Uncomment to test a specific symbol/date in detail
    # test_specific_symbol_date('NFLX', '2025-10-13')
