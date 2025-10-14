#!/usr/bin/env python3
"""
Alpaca Trades Data Downloader

This script downloads all trade data (activities) from an Alpaca account
and stores it in a local SQLite database for fast access.

Requirements:
    pip install alpaca-py requests pandas sqlite3

Usage:
    python alpaca_trades_downloader.py [start_date] [days_back]
    
Examples:
    python alpaca_trades_downloader.py                    # Last 7 days
    python alpaca_trades_downloader.py 2025-10-06        # From Oct 6th to now
    python alpaca_trades_downloader.py 2025-10-06 30     # From Oct 6th, 30 days back
"""

import os
import json
import sqlite3
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
import sys

# Add parent directory to path to import config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.config import ALPACA_KEY, ALPACA_SECRET, ALPACA_BASE_URL

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('alpaca_trades_download.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), 'trades.db')

class AlpacaTradesDownloader:
    """Class to handle downloading trade data from Alpaca API using official SDK"""
    
    def __init__(self, api_key: str, secret_key: str, base_url: str):
        """Initialize the Alpaca client"""
        try:
            # Set environment variable for base URL
            os.environ['APCA_API_BASE_URL'] = base_url
            
            # Import here to avoid issues if alpaca-py is not installed
            from alpaca.trading.client import TradingClient
            
            self.client = TradingClient(
                api_key=api_key,
                secret_key=secret_key,
                paper=False  # Set to True for paper trading
            )
            logger.info("Alpaca client initialized successfully")
            
        except ImportError:
            logger.error("alpaca-py package not found. Install with: pip install alpaca-py")
            raise
        except Exception as e:
            logger.error(f"Error initializing Alpaca client: {e}")
            raise
    
    def init_database(self):
        """Initialize SQLite database for trades"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT UNIQUE NOT NULL,
                client_order_id TEXT,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                qty REAL NOT NULL,
                filled_qty REAL,
                filled_avg_price REAL,
                status TEXT NOT NULL,
                order_type TEXT,
                order_class TEXT,
                time_in_force TEXT,
                limit_price REAL,
                stop_price REAL,
                created_at TEXT,
                submitted_at TEXT,
                filled_at TEXT,
                canceled_at TEXT,
                failed_at TEXT,
                expired_at TEXT,
                updated_at TEXT,
                extended_hours BOOLEAN,
                notional REAL,
                date_added TEXT NOT NULL,
                UNIQUE(order_id)
            )
        ''')
        
        # Create indexes for faster queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_symbol ON orders(symbol)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON orders(created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_filled_at ON orders(filled_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON orders(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_date ON orders(date(created_at))')
        
        conn.commit()
        conn.close()
        logger.info("Trades database initialized")
    
    def get_date_range(self, start_date: str = None, days_back: int = 7) -> tuple:
        """Calculate the date range for downloading"""
        if start_date:
            # Parse start date
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                end_dt = datetime.now(timezone.utc)
            except ValueError:
                logger.error(f"Invalid date format: {start_date}. Use YYYY-MM-DD format.")
                raise
        else:
            # Default to last N days
            end_dt = datetime.now(timezone.utc)
            start_dt = end_dt - timedelta(days=days_back)
        
        # Format dates for Alpaca API (ISO format with timezone)
        start_date_str = start_dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        end_date_str = end_dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        
        logger.info(f"Date range: {start_dt.strftime('%Y-%m-%d')} to {end_dt.strftime('%Y-%m-%d')}")
        return start_date_str, end_date_str
    
    def fetch_orders(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Fetch all orders within the specified date range using Alpaca SDK"""
        try:
            from alpaca.trading.requests import GetOrdersRequest
            from alpaca.trading.enums import QueryOrderStatus
            
            # Create request to get all orders in the date range
            request_params = GetOrdersRequest(
                status=QueryOrderStatus.ALL,  # Get all orders regardless of status
                after=start_date,
                until=end_date,
                limit=500,  # Maximum limit per request
                nested=True  # Include nested data
            )
            
            logger.info("Fetching orders from Alpaca API...")
            orders = self.client.get_orders(request_params)
            
            # Convert orders to dictionaries for easier processing
            orders_data = []
            for order in orders:
                order_dict = {
                    'id': order.id,
                    'client_order_id': order.client_order_id,
                    'created_at': order.created_at.isoformat() if order.created_at else None,
                    'updated_at': order.updated_at.isoformat() if order.updated_at else None,
                    'submitted_at': order.submitted_at.isoformat() if order.submitted_at else None,
                    'filled_at': order.filled_at.isoformat() if order.filled_at else None,
                    'expired_at': order.expired_at.isoformat() if order.expired_at else None,
                    'canceled_at': order.canceled_at.isoformat() if order.canceled_at else None,
                    'failed_at': order.failed_at.isoformat() if order.failed_at else None,
                    'replaced_at': order.replaced_at.isoformat() if order.replaced_at else None,
                    'replaced_by': order.replaced_by,
                    'replaces': order.replaces,
                    'asset_id': order.asset_id,
                    'symbol': order.symbol,
                    'asset_class': order.asset_class,
                    'notional': order.notional,
                    'qty': order.qty,
                    'filled_qty': order.filled_qty,
                    'filled_avg_price': order.filled_avg_price,
                    'order_class': order.order_class,
                    'order_type': order.order_type,
                    'type': order.type,
                    'side': order.side,
                    'time_in_force': order.time_in_force,
                    'limit_price': order.limit_price,
                    'stop_price': order.stop_price,
                    'status': order.status,
                    'extended_hours': order.extended_hours,
                    'legs': [self._serialize_leg(leg) for leg in order.legs] if order.legs else None,
                    'trail_percent': order.trail_percent,
                    'trail_price': order.trail_price,
                    'hwm': order.hwm
                }
                orders_data.append(order_dict)
            
            logger.info(f"Successfully fetched {len(orders_data)} orders")
            return orders_data
            
        except Exception as e:
            logger.error(f"Error fetching orders: {e}")
            raise
    
    def _serialize_leg(self, leg) -> Dict[str, Any]:
        """Serialize order leg data"""
        return {
            'id': leg.id,
            'client_order_id': leg.client_order_id,
            'created_at': leg.created_at.isoformat() if leg.created_at else None,
            'updated_at': leg.updated_at.isoformat() if leg.updated_at else None,
            'submitted_at': leg.submitted_at.isoformat() if leg.submitted_at else None,
            'filled_at': leg.filled_at.isoformat() if leg.filled_at else None,
            'expired_at': leg.expired_at.isoformat() if leg.expired_at else None,
            'canceled_at': leg.canceled_at.isoformat() if leg.canceled_at else None,
            'failed_at': leg.failed_at.isoformat() if leg.failed_at else None,
            'replaced_at': leg.replaced_at.isoformat() if leg.replaced_at else None,
            'replaced_by': leg.replaced_by,
            'replaces': leg.replaces,
            'asset_id': leg.asset_id,
            'symbol': leg.symbol,
            'asset_class': leg.asset_class,
            'notional': leg.notional,
            'qty': leg.qty,
            'filled_qty': leg.filled_qty,
            'filled_avg_price': leg.filled_avg_price,
            'order_class': leg.order_class,
            'order_type': leg.order_type,
            'type': leg.type,
            'side': leg.side,
            'time_in_force': leg.time_in_force,
            'limit_price': leg.limit_price,
            'stop_price': leg.stop_price,
            'status': leg.status,
            'extended_hours': leg.extended_hours,
            'trail_percent': leg.trail_percent,
            'trail_price': leg.trail_price,
            'hwm': leg.hwm
        }
    
    def save_orders_to_database(self, orders: List[Dict[str, Any]]):
        """Save orders to SQLite database"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        saved_count = 0
        skipped_count = 0
        
        for order in orders:
            try:
                # Insert order - handle None values properly
                # Convert datetime objects to strings if they exist
                def safe_datetime_to_str(dt):
                    if dt is None:
                        return None
                    if hasattr(dt, 'isoformat'):
                        return dt.isoformat()
                    return str(dt) if dt else None
                
                cursor.execute('''
                    INSERT OR IGNORE INTO orders (
                        order_id, client_order_id, symbol, side, qty, filled_qty, filled_avg_price,
                        status, order_type, order_class, time_in_force, limit_price, stop_price,
                        created_at, submitted_at, filled_at, canceled_at, failed_at, expired_at,
                        updated_at, extended_hours, notional, date_added
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    str(order.get('id', '')),
                    str(order.get('client_order_id', '')),
                    str(order.get('symbol', '')),
                    str(order.get('side', '')),
                    float(order.get('qty', 0)) if order.get('qty') is not None else 0.0,
                    float(order.get('filled_qty', 0)) if order.get('filled_qty') is not None else None,
                    float(order.get('filled_avg_price', 0)) if order.get('filled_avg_price') is not None else None,
                    str(order.get('status', '')),
                    str(order.get('order_type', '')),
                    str(order.get('order_class', '')),
                    str(order.get('time_in_force', '')),
                    float(order.get('limit_price', 0)) if order.get('limit_price') is not None else None,
                    float(order.get('stop_price', 0)) if order.get('stop_price') is not None else None,
                    safe_datetime_to_str(order.get('created_at')),
                    safe_datetime_to_str(order.get('submitted_at')),
                    safe_datetime_to_str(order.get('filled_at')),
                    safe_datetime_to_str(order.get('canceled_at')),
                    safe_datetime_to_str(order.get('failed_at')),
                    safe_datetime_to_str(order.get('expired_at')),
                    safe_datetime_to_str(order.get('updated_at')),
                    1 if order.get('extended_hours') else 0,  # Convert boolean to int for SQLite
                    float(order.get('notional', 0)) if order.get('notional') is not None else None,
                    datetime.now(timezone.utc).isoformat()
                ))
                
                if cursor.rowcount > 0:
                    saved_count += 1
                else:
                    skipped_count += 1
                    
            except Exception as e:
                logger.error(f"Error saving order {order.get('id', 'unknown')}: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        logger.info(f"Saved {saved_count} new orders, skipped {skipped_count} existing orders")
        return saved_count, skipped_count
    
    def get_trades_summary(self) -> Dict[str, Any]:
        """Get summary of all trades in database"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                symbol,
                COUNT(*) as trade_count,
                SUM(value) as net_value,
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
    
    def get_date_range_from_db(self) -> Dict[str, str]:
        """Get the date range of trades in database"""
        conn = sqlite3.connect(DB_PATH)
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
        
        if row and row[0]:
            return {
                'earliest_date': row[0],
                'latest_date': row[1],
                'total_trades': row[2]
            }
        else:
            return {
                'earliest_date': 'No data',
                'latest_date': 'No data',
                'total_trades': 0
            }
    
    def download_trades(self, start_date: str = None, days_back: int = 7):
        """Main method to download trades and save to database"""
        try:
            # Initialize database
            self.init_database()
            
            # Get date range
            start_date_str, end_date_str = self.get_date_range(start_date, days_back)
            
            # Fetch orders
            orders = self.fetch_orders(start_date_str, end_date_str)
            
            if not orders:
                logger.info("No orders found in the specified date range")
                return []
            
            # Save to database
            saved_count, skipped_count = self.save_orders_to_database(orders)
            
            # Get summary
            summary = self.get_trades_summary()
            date_range = self.get_date_range_from_db()
            
            logger.info(f"Download completed: {saved_count} new trades saved, {skipped_count} existing trades skipped")
            
            return {
                'orders': orders,
                'saved_count': saved_count,
                'skipped_count': skipped_count,
                'summary': summary,
                'date_range': date_range
            }
            
        except Exception as e:
            logger.error(f"Error in download_trades: {e}")
            raise

def main():
    """Main function to execute the trades download process"""
    try:
        logger.info("Starting Alpaca trades data download...")
        
        # Parse command line arguments
        start_date = None
        days_back = 7
        
        if len(sys.argv) > 1:
            start_date = sys.argv[1]
        if len(sys.argv) > 2:
            days_back = int(sys.argv[2])
        
        # Initialize the downloader
        downloader = AlpacaTradesDownloader(
            api_key=ALPACA_KEY,
            secret_key=ALPACA_SECRET,
            base_url=ALPACA_BASE_URL
        )
        
        # Download trades
        result = downloader.download_trades(start_date, days_back)
        
        if not result['orders']:
            logger.info("No orders found in the specified date range")
            return
        
        # Display summary
        print("\n" + "="*60)
        print("ALPACA TRADES DOWNLOAD SUMMARY")
        print("="*60)
        print(f"Total orders downloaded: {len(result['orders'])}")
        print(f"New orders saved: {result['saved_count']}")
        print(f"Existing orders skipped: {result['skipped_count']}")
        print(f"Date range: {result['date_range']['earliest_date']} to {result['date_range']['latest_date']}")
        print(f"Total trades in database: {result['date_range']['total_trades']}")
        print(f"Symbols traded: {len(result['summary'])}")
        
        print("\nTop symbols by trade count:")
        for symbol, data in list(result['summary'].items())[:10]:
            print(f"  {symbol}: {data['trade_count']} trades, ${data['net_value']:.2f} net value")
        
        print(f"\nDatabase saved to: {DB_PATH}")
        print("="*60)
        
        logger.info("Trades data download completed successfully")
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        raise

if __name__ == "__main__":
    main()
