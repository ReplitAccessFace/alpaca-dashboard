#!/usr/bin/env python3
"""
Simple Alpaca Orders Downloader

This script downloads all order data from an Alpaca account and exports it to CSV,
exactly like your original script but integrated with our system.

Usage:
    python simple_orders_downloader.py [start_date] [days_back]
    
Examples:
    python simple_orders_downloader.py                    # Last 7 days
    python simple_orders_downloader.py 2025-10-06        # From Oct 6th to now
    python simple_orders_downloader.py 2025-10-06 30     # From Oct 6th, 30 days back
"""

import os
import json
import csv
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
import sys
import pandas as pd

# Add parent directory to path to import config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.config import ALPACA_KEY, ALPACA_SECRET, ALPACA_BASE_URL

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('alpaca_orders_download.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SimpleAlpacaOrdersDownloader:
    """Class to handle downloading order data from Alpaca API using official SDK"""
    
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
    
    def export_to_csv(self, orders_data: List[Dict[str, Any]], filename: str = None) -> str:
        """Export orders data to CSV file"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'alpaca_orders_{timestamp}.csv'
        
        if not orders_data:
            logger.warning("No orders data to export")
            return filename
        
        # Flatten the data for CSV export
        flattened_data = []
        for order in orders_data:
            flat_order = order.copy()
            # Convert legs to string representation for CSV
            if flat_order['legs']:
                flat_order['legs'] = json.dumps(flat_order['legs'])
            flattened_data.append(flat_order)
        
        # Create DataFrame and export to CSV
        df = pd.DataFrame(flattened_data)
        df.to_csv(filename, index=False)
        logger.info(f"Orders data exported to CSV: {filename}")
        return filename
    
    def export_to_json(self, orders_data: List[Dict[str, Any]], filename: str = None) -> str:
        """Export orders data to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'alpaca_orders_{timestamp}.json'
        
        with open(filename, 'w') as f:
            json.dump(orders_data, f, indent=2, default=str)
        
        logger.info(f"Orders data exported to JSON: {filename}")
        return filename
    
    def generate_summary(self, orders_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a summary of the orders data"""
        if not orders_data:
            return {"total_orders": 0}
        
        summary = {
            "total_orders": len(orders_data),
            "date_range": {
                "start": min(order['created_at'] for order in orders_data if order['created_at']),
                "end": max(order['created_at'] for order in orders_data if order['created_at'])
            },
            "status_breakdown": {},
            "side_breakdown": {},
            "symbol_breakdown": {},
            "total_notional": 0,
            "total_filled_notional": 0
        }
        
        # Calculate breakdowns
        for order in orders_data:
            # Status breakdown
            status = order.get('status', 'unknown')
            summary['status_breakdown'][status] = summary['status_breakdown'].get(status, 0) + 1
            
            # Side breakdown
            side = order.get('side', 'unknown')
            summary['side_breakdown'][side] = summary['side_breakdown'].get(side, 0) + 1
            
            # Symbol breakdown
            symbol = order.get('symbol', 'unknown')
            summary['symbol_breakdown'][symbol] = summary['symbol_breakdown'].get(symbol, 0) + 1
            
            # Notional calculations
            notional = order.get('notional') or 0
            if isinstance(notional, str):
                try:
                    notional = float(notional)
                except (ValueError, TypeError):
                    notional = 0
            summary['total_notional'] += notional
            
            filled_qty = order.get('filled_qty') or 0
            filled_avg_price = order.get('filled_avg_price') or 0
            
            # Convert to float if they're strings
            if isinstance(filled_qty, str):
                try:
                    filled_qty = float(filled_qty)
                except (ValueError, TypeError):
                    filled_qty = 0
            
            if isinstance(filled_avg_price, str):
                try:
                    filled_avg_price = float(filled_avg_price)
                except (ValueError, TypeError):
                    filled_avg_price = 0
            
            filled_notional = filled_qty * filled_avg_price
            summary['total_filled_notional'] += filled_notional
        
        return summary

def main():
    """Main function to execute the order download process"""
    try:
        logger.info("Starting Alpaca order data download...")
        
        # Parse command line arguments
        start_date = None
        days_back = 7
        
        if len(sys.argv) > 1:
            start_date = sys.argv[1]
        if len(sys.argv) > 2:
            days_back = int(sys.argv[2])
        
        # Initialize the downloader
        downloader = SimpleAlpacaOrdersDownloader(
            api_key=ALPACA_KEY,
            secret_key=ALPACA_SECRET,
            base_url=ALPACA_BASE_URL
        )
        
        # Get date range
        start_date_str, end_date_str = downloader.get_date_range(start_date, days_back)
        
        # Fetch orders
        orders_data = downloader.fetch_orders(start_date_str, end_date_str)
        
        if not orders_data:
            logger.info("No orders found in the specified date range")
            return
        
        # Export data
        csv_filename = downloader.export_to_csv(orders_data)
        json_filename = downloader.export_to_json(orders_data)
        
        # Generate and display summary
        summary = downloader.generate_summary(orders_data)
        
        print("\n" + "="*50)
        print("ALPACA ORDERS DOWNLOAD SUMMARY")
        print("="*50)
        print(f"Total Orders: {summary['total_orders']}")
        print(f"Date Range: {summary['date_range']['start']} to {summary['date_range']['end']}")
        print(f"Total Notional: ${summary['total_notional']:,.2f}")
        print(f"Total Filled Notional: ${summary['total_filled_notional']:,.2f}")
        
        print("\nStatus Breakdown:")
        for status, count in summary['status_breakdown'].items():
            print(f"  {status}: {count}")
        
        print("\nSide Breakdown:")
        for side, count in summary['side_breakdown'].items():
            print(f"  {side}: {count}")
        
        print("\nTop Symbols:")
        sorted_symbols = sorted(summary['symbol_breakdown'].items(), key=lambda x: x[1], reverse=True)
        for symbol, count in sorted_symbols[:10]:  # Show top 10
            print(f"  {symbol}: {count}")
        
        print(f"\nFiles created:")
        print(f"  CSV: {csv_filename}")
        print(f"  JSON: {json_filename}")
        print("="*50)
        
        logger.info("Order data download completed successfully")
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        raise

if __name__ == "__main__":
    main()
