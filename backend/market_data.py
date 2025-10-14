import sqlite3
import requests
import json
from datetime import datetime, timedelta, timezone
from typing import List, Dict
from config import MARKET_API_KEY, MARKET_API_SECRET, MARKET_BASE_URL

class MarketDataManager:
    def __init__(self, db_path="market_data.db"):
        self.db_path = db_path
        self.api_key = MARKET_API_KEY
        self.api_secret = MARKET_API_SECRET
        self.base_url = MARKET_BASE_URL
        self.init_database()
    
    def init_database(self):
        """Initialize the database with market data table"""
        conn = sqlite3.connect(self.db_path)
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol, timestamp)
            )
        ''')
        
        # Create index for faster queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_symbol_timestamp 
            ON market_data(symbol, timestamp)
        ''')
        
        conn.commit()
        conn.close()
    
    def get_market_data_from_api(self, symbol: str, start_date: str, end_date: str = None) -> List[Dict]:
        """Fetch market data from Alpaca using the official SDK"""
        try:
            # Import Alpaca SDK components
            import pandas as pd
            from alpaca.data import StockHistoricalDataClient
            from alpaca.data.requests import StockBarsRequest
            from alpaca.data.timeframe import TimeFrame
            
            # Initialize the Alpaca data client
            client = StockHistoricalDataClient(self.api_key, self.api_secret)
            
            # Convert date to timezone-aware timestamps
            start_timestamp = pd.Timestamp(f'{start_date} 09:30:00', tz='America/New_York')
            end_timestamp = pd.Timestamp(f'{start_date} 16:00:00', tz='America/New_York')
            
            print(f"Fetching {symbol} data from {start_timestamp} to {end_timestamp}")
            
            # Create a request for minute-level bars
            request_params = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=TimeFrame.Minute,
                start=start_timestamp,
                end=end_timestamp
            )
            
            # Fetch the data
            bars = client.get_stock_bars(request_params)
            df = bars.df
            
            print(f"Received {len(df)} data points for {symbol}")
            
            if len(df) == 0:
                print(f"No data received for {symbol} on {start_date}")
                return []
            
            # Convert DataFrame to our expected format
            formatted_data = []
            for (symbol_name, timestamp), row in df.iterrows():
                formatted_data.append({
                    "symbol": symbol_name,
                    "timestamp": int(timestamp.timestamp()),
                    "open": float(row['open']),
                    "high": float(row['high']),
                    "low": float(row['low']),
                    "close": float(row['close']),
                    "volume": int(row['volume'])
                })
            
            return formatted_data
            
        except Exception as e:
            print(f"Error fetching market data using SDK: {e}")
            return []
    
    def store_market_data(self, data: List[Dict]):
        """Store market data in the database"""
        if not data:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            for item in data:
                cursor.execute('''
                    INSERT OR REPLACE INTO market_data 
                    (symbol, timestamp, open, high, low, close, volume)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    item["symbol"],
                    item["timestamp"],
                    item["open"],
                    item["high"],
                    item["low"],
                    item["close"],
                    item["volume"]
                ))
            
            conn.commit()
            print(f"Stored {len(data)} market data points")
            
        except Exception as e:
            print(f"Error storing market data: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def get_market_data_from_db(self, symbol: str, start_date: str = None, end_date: str = None) -> List[Dict]:
        """Retrieve market data from the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM market_data WHERE symbol = ?"
        params = [symbol]
        
        if start_date:
            # Use SQL date function to filter by date only
            query += " AND date(datetime(timestamp, 'unixepoch')) = ?"
            params.append(start_date)
        
        query += " ORDER BY timestamp ASC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        data = []
        for row in rows:
            data.append({
                "symbol": row[1],
                "timestamp": row[2],
                "open": row[3],
                "high": row[4],
                "low": row[5],
                "close": row[6],
                "volume": row[7]
            })
        
        return data

    def filter_trading_hours(self, data: List[Dict]) -> List[Dict]:
        """Filter data to trading hours: 1:30 PM UTC to 9:00 PM UTC (9:30 AM ET to 5:00 PM ET)"""
        if not data:
            return data
        
        filtered_data = []
        for item in data:
            # Convert timestamp to datetime (UTC)
            dt_utc = datetime.fromtimestamp(item["timestamp"], tz=timezone.utc)
            
            # Check if time is between 1:30 PM and 9:00 PM UTC (9:30 AM ET to 5:00 PM ET)
            hour = dt_utc.hour
            minute = dt_utc.minute
            
            # Market hours: 9:30 AM ET to 4:00 PM ET = 1:30 PM UTC to 8:00 PM UTC
            # But we'll use 1:30 PM to 9:00 PM UTC to be safe
            if (hour > 13) or (hour == 13 and minute >= 30) or (hour < 21):
                filtered_data.append(item)
        
        return filtered_data
    
    def download_and_store_market_data(self, symbol: str, start_date: str = None):
        """Get market data from database, download if not available"""
        # Use today's date if no date provided
        if start_date is None:
            from datetime import datetime
            start_date = datetime.now().strftime("%Y-%m-%d")
        
        print(f"Getting market data for {symbol} from {start_date}")
        
        # Get data from database - now filters by date only
        existing_data = self.get_market_data_from_db(symbol, start_date)
        if existing_data:
            print(f"Found {len(existing_data)} existing 1-minute data points for {symbol}")
            # Convert to the format expected by the chart
            formatted_data = []
            for item in existing_data:
                formatted_data.append({
                    "time": item["timestamp"],
                    "open": item["open"],
                    "high": item["high"],
                    "low": item["low"],
                    "close": item["close"],
                    "volume": item["volume"]
                })
            return formatted_data
        else:
            print(f"No data found for {symbol} on {start_date}, attempting to download...")
            # Try to download market data for this date
            try:
                # Download market data from API
                api_data = self.get_market_data_from_api(symbol, start_date, start_date)
                if api_data:
                    # Store the downloaded data
                    self.store_market_data(api_data)
                    print(f"Downloaded and stored {len(api_data)} data points for {symbol} on {start_date}")
                    
                    # Get the data from database again
                    existing_data = self.get_market_data_from_db(symbol, start_date)
                    if existing_data:
                        formatted_data = []
                        for item in existing_data:
                            formatted_data.append({
                                "time": item["timestamp"],
                                "open": item["open"],
                                "high": item["high"],
                                "low": item["low"],
                                "close": item["close"],
                                "volume": item["volume"]
                            })
                        return formatted_data
                
                print(f"Could not download market data for {symbol} on {start_date}")
                return []
            except Exception as e:
                print(f"Error downloading market data for {symbol} on {start_date}: {e}")
                return []
    
    def get_available_symbols(self) -> List[str]:
        """Get list of symbols that have data in the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT DISTINCT symbol FROM market_data ORDER BY symbol")
        symbols = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return symbols
