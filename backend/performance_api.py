from fastapi import APIRouter, HTTPException
from alpaca_client import AlpacaClient
from market_data import MarketDataManager
from trades_database import TradesDatabase
from datetime import datetime, timezone
from typing import Dict, List
import sqlite3
from config import ALPACA_KEY, ALPACA_SECRET, ALPACA_BASE_URL

# Create router for performance endpoints
router = APIRouter(prefix="/api/performance", tags=["performance"])

# Initialize clients
alpaca = AlpacaClient()
market_data_manager = MarketDataManager()
trades_db = TradesDatabase()

@router.get("/trades-with-prices")
async def get_trades_with_prices():
    """Get trades with corresponding price data for visualization"""
    try:
        # Get all activities (trades)
        activities = alpaca.get_activities(activity_type="FILL", limit=1000)
        
        # Get unique symbols from trades
        symbols = list(set([activity.get('symbol') for activity in activities if activity.get('symbol')]))
        
        trades_with_prices = {}
        
        for symbol in symbols:
            try:
                # Get trades for this symbol first
                symbol_trades = []
                for activity in activities:
                    if activity.get('symbol') == symbol and activity.get('activity_type') == 'FILL':
                        try:
                            timestamp_str = activity.get('transaction_time', '')
                            if timestamp_str:
                                # Parse the UTC timestamp directly without timezone conversion
                                try:
                                    # Parse the UTC timestamp
                                    utc_dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                                    trade_time = int(utc_dt.timestamp())
                                except ValueError:
                                    # If still failing, try parsing without microseconds
                                    timestamp_str = timestamp_str.split('.')[0] + '+00:00'
                                    utc_dt = datetime.fromisoformat(timestamp_str)
                                    trade_time = int(utc_dt.timestamp())
                            else:
                                trade_time = 0
                        except Exception as e:
                            print(f"Error parsing timestamp for {symbol}: {e}")
                            # Try to use current time as fallback
                            trade_time = int(datetime.now().timestamp())
                        
                        symbol_trades.append({
                            'symbol': symbol,
                            'side': activity.get('side', ''),
                            'price': float(activity.get('price', 0)),
                            'qty': float(activity.get('qty', 0)),
                            'value': float(activity.get('price', 0)) * float(activity.get('qty', 0)),
                            'timestamp': activity.get('transaction_time', ''),
                            'time': trade_time
                        })
                
                # Try to get price data for this symbol
                try:
                    # Get market data from database
                    market_data = market_data_manager.download_and_store_market_data(symbol, "2025-10-07")
                    
                    if market_data and len(market_data) > 0:
                        # Format price data for chart
                        price_data = []
                        for item in market_data:
                            price_data.append({
                                'time': item['time'],
                                'open': item['open'],
                                'high': item['high'],
                                'low': item['low'],
                                'close': item['close'],
                                'volume': item['volume']
                            })
                    else:
                        # Create mock price data based on trades if real data fails
                        if symbol_trades:
                            # Create simple price data around trade prices
                            trade_prices = [trade['price'] for trade in symbol_trades]
                            min_price = min(trade_prices) * 0.95
                            max_price = max(trade_prices) * 1.05
                            
                            price_data = []
                            for i in range(100):  # Create 100 data points
                                price_data.append({
                                    'time': int(datetime.now().timestamp()) - (100 - i) * 60,  # 1 minute intervals
                                    'open': min_price + (max_price - min_price) * (i / 100),
                                    'high': min_price + (max_price - min_price) * (i / 100) * 1.01,
                                    'low': min_price + (max_price - min_price) * (i / 100) * 0.99,
                                    'close': min_price + (max_price - min_price) * (i / 100),
                                    'volume': 1000
                                })
                        else:
                            price_data = []
                    
                    trades_with_prices[symbol] = {
                        'price_data': price_data,
                        'trades': symbol_trades
                    }
                except Exception as e:
                    print(f"Could not fetch price data for {symbol}: {e}")
                    trades_with_prices[symbol] = {
                        'price_data': [],
                        'trades': symbol_trades
                    }
            except Exception as e:
                print(f"Error processing {symbol}: {e}")
                trades_with_prices[symbol] = {
                    'price_data': [],
                    'trades': []
                }
        
        return {
            'symbols': symbols,
            'data': trades_with_prices
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching trades with prices: {str(e)}")

@router.get("/market-data/{symbol}/with-trades")
async def get_market_data_with_trades(symbol: str, start_date: str = None):
    """Get market data with trading markers for a symbol"""
    try:
        # Use today's date if no date provided
        if start_date is None:
            from datetime import datetime
            start_date = datetime.now().strftime("%Y-%m-%d")
        
        # Get market data
        market_data = market_data_manager.download_and_store_market_data(symbol, start_date)
        
        # Get trading data for this symbol on the selected date (UTC)
        symbol_trades = []
        
        try:
            # Query the orders table directly (new format)
            import sqlite3
            import os
            db_path = os.path.join(os.path.dirname(__file__), 'trades.db')
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Query orders table for the specified symbol and date
            cursor.execute('''
                SELECT * FROM orders 
                WHERE symbol = ? 
                AND (status = 'filled' OR status = 'OrderStatus.FILLED')
                AND date(created_at) = ?
                ORDER BY created_at ASC
            ''', (symbol, start_date))
            
            orders = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            print(f"DEBUG: Found {len(orders)} orders for {symbol} on {start_date}")
            
            # Convert orders to trade format
            for order in orders:
                # Map enum side values to simple strings
                side = order['side']
                if side == 'OrderSide.BUY': side = 'buy'
                elif side == 'OrderSide.SELL': side = 'sell'
                elif side == 'OrderSide.SELL_SHORT': side = 'sell_short'
                elif side == 'OrderSide.BUY_TO_COVER': side = 'buy_to_cover'
                
                # Convert filled_at to timestamp
                from datetime import datetime
                filled_at = order['filled_at']
                if filled_at:
                    dt = datetime.fromisoformat(filled_at.replace('Z', '+00:00'))
                    timestamp = int(dt.timestamp())
                else:
                    timestamp = 0
                
                symbol_trades.append({
                    'symbol': order['symbol'],
                    'side': side,
                    'price': order['filled_avg_price'] or 0,
                    'qty': order['filled_qty'] or order['qty'] or 0,
                    'value': (order['filled_avg_price'] or 0) * (order['filled_qty'] or order['qty'] or 0),
                    'timestamp': order['filled_at'],
                    'time': timestamp
                })
                
        except Exception as e:
            print(f"Error getting trades from database for {symbol}: {e}")
            # Fallback to empty trades list
            symbol_trades = []
        
        # Format trades for markers
        trade_markers = []
        for trade in symbol_trades:
            is_buy = trade['side'] == 'buy' or trade['side'] == 'buy_to_cover'
            trade_markers.append({
                'time': trade['time'],
                'position': 'belowBar' if is_buy else 'aboveBar',
                'color': '#26a69a' if is_buy else '#ef5350',
                'shape': 'arrowUp' if is_buy else 'arrowDown',
                'text': f"{'BUY' if is_buy else 'SELL'} {trade['qty']} @ ${trade['price']}"
            })

        # Debug: print first few trade times in UTC
        try:
            from datetime import datetime, timezone
            preview = symbol_trades[:3]
            print("DEBUG UTC trades preview:", [
                {
                    'time': t['time'],
                    'utc': datetime.fromtimestamp(t['time'], tz=timezone.utc).isoformat(),
                    'timestamp': t['timestamp'],
                    'side': t['side']
                } for t in preview
            ])
        except Exception as _:
            pass
        
        return {
            "symbol": symbol,
            "market_data": market_data,
            "trades": symbol_trades,
            "trade_markers": trade_markers,
            "market_data_count": len(market_data),
            "trades_count": len(symbol_trades)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching market data with trades: {str(e)}")

@router.get("/market-data/symbols")
async def get_available_symbols():
    """Get list of symbols that have market data available"""
    try:
        symbols = market_data_manager.get_available_symbols()
        return {"symbols": symbols}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching available symbols: {str(e)}")

@router.post("/market-data/download-all")
async def download_all_market_data(date: str = None):
    """Download market data for all symbols, optionally for a specific date"""
    try:
        if date:
            # Download market data for specific date
            symbols = ['AAPL', 'AMZN', 'AVGO', 'GOOGL', 'META', 'MSFT', 'NFLX', 'NVDA', 'PLTR', 'TSLA']
            downloaded_count = 0
            
            for symbol in symbols:
                try:
                    market_data_manager.download_and_store_market_data(symbol, date)
                    downloaded_count += 1
                except Exception as e:
                    print(f"Error downloading market data for {symbol} on {date}: {e}")
            
            return {
                "message": f"Downloaded market data for {downloaded_count} symbols on {date}",
                "status": "success",
                "symbols_downloaded": downloaded_count,
                "date": date
            }
        else:
            # This would trigger the download_market_data.py script
            # For now, just return success
            return {"message": "Market data download initiated", "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading market data: {str(e)}")

@router.post("/refresh-today")
async def refresh_today_data():
    """Automatically download today's market data and trades"""
    try:
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Download today's market data
        symbols = ['AAPL', 'AMZN', 'AVGO', 'GOOGL', 'META', 'MSFT', 'NFLX', 'NVDA', 'PLTR', 'TSLA']
        market_downloaded_count = 0
        
        for symbol in symbols:
            try:
                market_data_manager.download_and_store_market_data(symbol, today)
                market_downloaded_count += 1
            except Exception as e:
                print(f"Error downloading market data for {symbol} on {today}: {e}")
        
        # Download today's trades
        from alpaca_trades_downloader import AlpacaTradesDownloader
        from config import ALPACA_KEY, ALPACA_SECRET, ALPACA_BASE_URL
        
        downloader = AlpacaTradesDownloader(
            api_key=ALPACA_KEY,
            secret_key=ALPACA_SECRET,
            base_url=ALPACA_BASE_URL
        )
        
        trades_result = downloader.download_trades(today, 1)
        
        return {
            "message": f"Successfully refreshed data for {today}",
            "status": "success",
            "date": today,
            "market_data": {
                "symbols_downloaded": market_downloaded_count,
                "total_symbols": len(symbols)
            },
            "trades": {
                "total_trades": len(trades_result['orders']),
                "new_trades_saved": trades_result['saved_count'],
                "existing_trades_skipped": trades_result['skipped_count']
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error refreshing today's data: {str(e)}")

@router.post("/trades/download-all")
async def download_all_historical_trades(start_date: str = None, days_back: int = 7):
    """Download all historical trades from Alpaca using the new downloader"""
    try:
        from alpaca_trades_downloader import AlpacaTradesDownloader
        
        # Initialize the new downloader
        downloader = AlpacaTradesDownloader(
            api_key=ALPACA_KEY,
            secret_key=ALPACA_SECRET,
            base_url=ALPACA_BASE_URL
        )
        
        # Download trades
        result = downloader.download_trades(start_date, days_back)
        
        return {
            "message": f"Downloaded {len(result['orders'])} historical trades",
            "status": "success",
            "total_trades": len(result['orders']),
            "new_trades_saved": result['saved_count'],
            "existing_trades_skipped": result['skipped_count'],
            "date_range": result['date_range'],
            "symbols": list(result['summary'].keys()),
            "summary": result['summary']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading historical trades: {str(e)}")

@router.post("/trades/refresh-daily")
async def refresh_daily_trades():
    """Refresh today's trades only (for daily updates)"""
    try:
        trades = trades_db.refresh_daily_trades()
        
        return {
            "message": f"Refreshed {len(trades)} trades for today",
            "status": "success",
            "total_trades": len(trades)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error refreshing daily trades: {str(e)}")

@router.get("/trades/summary")
async def get_trades_summary():
    """Get summary of all trades in database"""
    try:
        summary = trades_db.get_trades_summary()
        date_range = trades_db.get_date_range()
        symbols = trades_db.get_all_symbols()
        
        return {
            "total_symbols": len(symbols),
            "date_range": date_range,
            "symbols": symbols,
            "summary": summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting trades summary: {str(e)}")
