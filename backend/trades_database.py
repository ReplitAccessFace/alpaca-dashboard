#!/usr/bin/env python3
import sqlite3
import requests
from datetime import datetime, timezone, timedelta
from typing import List, Dict
import sys
import os

# Add parent directory to path to import config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.config import ALPACA_KEY, ALPACA_SECRET, ALPACA_BASE_URL

DB_PATH = os.path.join(os.path.dirname(__file__), 'trades.db')

class TradesDatabase:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.api_key = ALPACA_KEY
        self.api_secret = ALPACA_SECRET
        self.base_url = ALPACA_BASE_URL
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database for trades"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id TEXT UNIQUE NOT NULL,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                price REAL NOT NULL,
                qty REAL NOT NULL,
                value REAL NOT NULL,
                transaction_time TEXT NOT NULL,
                transaction_timestamp INTEGER NOT NULL,
                activity_type TEXT NOT NULL,
                order_id TEXT,
                cum_qty REAL,
                leaves_qty REAL,
                net_amount REAL,
                per_share_amount REAL,
                date_added TEXT NOT NULL,
                UNIQUE(trade_id)
            )
        ''')
        
        # Create indexes for faster queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_symbol_timestamp 
            ON trades(symbol, transaction_timestamp)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_transaction_date 
            ON trades(date(transaction_time))
        ''')
        
        conn.commit()
        conn.close()
        print("Trades database initialized")
    
    def get_activities_from_alpaca(self, activity_type: str = "FILL", limit: int = 1000, page_token: str = None, 
                                 start_date: str = None, end_date: str = None) -> Dict:
        """Fetch activities from Alpaca API with optional date range"""
        url = f"{self.base_url}/account/activities"
        headers = {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.api_secret
        }
        
        params = {
            "activity_type": activity_type,
            "limit": limit
        }
        
        if page_token:
            params["page_token"] = page_token
        
        if start_date:
            # Convert date to ISO format with timezone
            if isinstance(start_date, str):
                params["after"] = f"{start_date}T00:00:00Z"
            else:
                params["after"] = start_date
        if end_date:
            # Convert date to ISO format with timezone
            if isinstance(end_date, str):
                params["until"] = f"{end_date}T23:59:59Z"
            else:
                params["until"] = end_date
        
        try:
            print(f"API Request URL: {url}")
            print(f"API Request Params: {params}")
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Alpaca API returns activities directly as a list, not wrapped in an object
            if isinstance(data, list):
                return {"activities": data, "next_page_token": None}
            else:
                return data
        except requests.exceptions.RequestException as e:
            print(f"Error fetching activities: {e}")
            return {"activities": [], "next_page_token": None}
    
    def download_all_historical_trades(self, start_date: str = None):
        """Download all historical trades from Alpaca"""
        if start_date:
            print(f"Starting download of historical trades from {start_date}...")
        else:
            print("Starting download of all historical trades...")
        
        all_trades = []
        page_token = None
        page_count = 0
        
        while True:
            page_count += 1
            print(f"Fetching page {page_count}...")
            
            data = self.get_activities_from_alpaca(limit=1000, page_token=page_token, start_date=start_date)
            activities = data.get("activities", [])
            
            if not activities:
                print("No more activities found")
                break
            
            print(f"Found {len(activities)} activities on page {page_count}")
            all_trades.extend(activities)
            
            page_token = data.get("next_page_token")
            if not page_token:
                print("No more pages")
                break
        
        print(f"Total activities downloaded: {len(all_trades)}")
        
        # Filter to only FILL activities (actual trades)
        fill_activities = [activity for activity in all_trades if activity.get('activity_type') == 'FILL']
        print(f"Total FILL activities (trades): {len(fill_activities)}")
        
        # Save to database
        self.save_trades_to_database(fill_activities)
        
        return fill_activities
    
    def download_historical_trades_from_date(self, start_date: str):
        """Download historical trades from a specific date onwards"""
        return self.download_all_historical_trades(start_date=start_date)
    
    def refresh_daily_trades(self):
        """Download only today's trades (for daily refresh)"""
        from datetime import datetime, timezone
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        print(f"Refreshing trades for {today}...")
        return self.download_all_historical_trades(start_date=today)
    
    def save_trades_to_database(self, trades: List[Dict]):
        """Save trades to SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        saved_count = 0
        skipped_count = 0
        
        for trade in trades:
            try:
                # Parse transaction time
                transaction_time = trade.get('transaction_time', '')
                if transaction_time:
                    try:
                        # Parse the UTC timestamp
                        utc_dt = datetime.fromisoformat(transaction_time.replace('Z', '+00:00'))
                        transaction_timestamp = int(utc_dt.timestamp())
                    except ValueError:
                        # If still failing, try parsing without microseconds
                        transaction_time_clean = transaction_time.split('.')[0] + '+00:00'
                        utc_dt = datetime.fromisoformat(transaction_time_clean)
                        transaction_timestamp = int(utc_dt.timestamp())
                else:
                    transaction_timestamp = 0
                
                # Insert trade
                cursor.execute('''
                    INSERT OR IGNORE INTO trades (
                        trade_id, symbol, side, price, qty, value,
                        transaction_time, transaction_timestamp, activity_type,
                        order_id, cum_qty, leaves_qty, net_amount, per_share_amount, date_added
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    trade.get('id', ''),
                    trade.get('symbol', ''),
                    trade.get('side', ''),
                    float(trade.get('price', 0)),
                    float(trade.get('qty', 0)),
                    float(trade.get('price', 0)) * float(trade.get('qty', 0)),
                    transaction_time,
                    transaction_timestamp,
                    trade.get('activity_type', ''),
                    trade.get('order_id', ''),
                    float(trade.get('cum_qty', 0)),
                    float(trade.get('leaves_qty', 0)),
                    float(trade.get('net_amount', 0)),
                    float(trade.get('per_share_amount', 0)),
                    datetime.now().isoformat()
                ))
                
                if cursor.rowcount > 0:
                    saved_count += 1
                else:
                    skipped_count += 1
                    
            except Exception as e:
                print(f"Error saving trade {trade.get('id', 'unknown')}: {e}")
                skipped_count += 1
        
        conn.commit()
        conn.close()
        
        print(f"Saved {saved_count} new trades, skipped {skipped_count} existing trades")
    
    def get_trades_by_date(self, date: str) -> List[Dict]:
        """Get all trades for a specific date"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM trades 
            WHERE date(transaction_time) = ? 
            ORDER BY transaction_timestamp ASC
        ''', (date,))
        
        rows = cursor.fetchall()
        conn.close()
        
        trades = []
        for row in rows:
            trades.append({
                'id': row[1],
                'symbol': row[2],
                'side': row[3],
                'price': row[4],
                'qty': row[5],
                'value': row[6],
                'transaction_time': row[7],
                'transaction_timestamp': row[8],
                'activity_type': row[9],
                'order_id': row[10],
                'cum_qty': row[11],
                'leaves_qty': row[12],
                'net_amount': row[13],
                'per_share_amount': row[14]
            })
        
        return trades
    
    def get_trades_by_symbol_and_date(self, symbol: str, date: str = None) -> List[Dict]:
        """Get trades for a specific symbol and date (or all dates if date is None)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if date is None:
            # Get all trades for this symbol
            cursor.execute('''
                SELECT * FROM trades 
                WHERE symbol = ? 
                ORDER BY transaction_timestamp ASC
            ''', (symbol,))
        else:
            # Get trades for specific date
            cursor.execute('''
                SELECT * FROM trades 
                WHERE symbol = ? AND date(transaction_time) = ? 
                ORDER BY transaction_timestamp ASC
            ''', (symbol, date))
        
        rows = cursor.fetchall()
        conn.close()
        
        trades = []
        for row in rows:
            trades.append({
                'id': row[1],
                'symbol': row[2],
                'side': row[3],
                'price': row[4],
                'qty': row[5],
                'value': row[6],
                'transaction_time': row[7],
                'transaction_timestamp': row[8],
                'activity_type': row[9],
                'order_id': row[10],
                'cum_qty': row[11],
                'leaves_qty': row[12],
                'net_amount': row[13],
                'per_share_amount': row[14]
            })
        
        return trades
    
    def get_all_symbols(self) -> List[str]:
        """Get list of all symbols that have trades"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT DISTINCT symbol FROM trades ORDER BY symbol')
        symbols = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return symbols
    
    def get_date_range(self) -> Dict:
        """Get the date range of available trades"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                MIN(date(transaction_time)) as earliest_date,
                MAX(date(transaction_time)) as latest_date,
                COUNT(*) as total_trades
            FROM trades
        ''')
        
        row = cursor.fetchone()
        conn.close()
        
        return {
            'earliest_date': row[0],
            'latest_date': row[1],
            'total_trades': row[2]
        }
    
    def get_trades_summary(self) -> Dict:
        """Get summary of all trades"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                symbol,
                COUNT(*) as trade_count,
                SUM(CASE WHEN side IN ('buy', 'buy_to_cover') THEN value ELSE -value END) as net_value,
                MIN(date(transaction_time)) as first_trade_date,
                MAX(date(transaction_time)) as last_trade_date
            FROM trades 
            GROUP BY symbol 
            ORDER BY trade_count DESC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        summary = {}
        for row in rows:
            summary[row[0]] = {
                'trade_count': row[1],
                'net_value': row[2],
                'first_trade_date': row[3],
                'last_trade_date': row[4]
            }
        
        return summary

def main():
    """Main function to download all historical trades"""
    import sys
    
    trades_db = TradesDatabase()
    
    print("=" * 60)
    print("ALPACA TRADES DOWNLOADER")
    print("=" * 60)
    
    # Check if a start date was provided as command line argument
    start_date = None
    if len(sys.argv) > 1:
        start_date = sys.argv[1]
        print(f"Downloading trades from {start_date}...")
    
    # Download historical trades
    if start_date:
        trades = trades_db.download_historical_trades_from_date(start_date)
    else:
        trades = trades_db.download_all_historical_trades()
    
    # Get summary
    summary = trades_db.get_trades_summary()
    date_range = trades_db.get_date_range()
    
    print("\n" + "=" * 60)
    print("DOWNLOAD SUMMARY")
    print("=" * 60)
    print(f"Total trades downloaded: {len(trades)}")
    print(f"Date range: {date_range['earliest_date']} to {date_range['latest_date']}")
    print(f"Symbols traded: {len(summary)}")
    
    print("\nTop symbols by trade count:")
    for symbol, data in list(summary.items())[:10]:
        print(f"  {symbol}: {data['trade_count']} trades, ${data['net_value']:.2f} net value")
    
    print(f"\nDatabase saved to: {DB_PATH}")
    print("=" * 60)

if __name__ == "__main__":
    main()
