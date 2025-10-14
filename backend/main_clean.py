from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from alpaca_client import AlpacaClient
from config import CORS_ORIGINS
from market_data import MarketDataManager
from performance_api import router as performance_router
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List

app = FastAPI(title="Alpaca Trading Dashboard API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Alpaca client
alpaca = AlpacaClient()

# Initialize Market Data Manager
market_data_manager = MarketDataManager()

# Include performance router
app.include_router(performance_router)

@app.get("/")
async def root():
    return {"message": "Alpaca Trading Dashboard API", "status": "running"}

@app.get("/api/account")
async def get_account():
    """Get account summary"""
    try:
        account = alpaca.get_account()
        return {
            "account_id": account.get("id"),
            "status": account.get("status"),
            "currency": account.get("currency"),
            "buying_power": float(account.get("buying_power", 0)),
            "cash": float(account.get("cash", 0)),
            "portfolio_value": float(account.get("portfolio_value", 0)),
            "equity": float(account.get("equity", 0)),
            "last_equity": float(account.get("last_equity", 0)),
            "day_trade_count": account.get("day_trade_count", 0),
            "pattern_day_trader": account.get("pattern_day_trader", False),
            "trading_blocked": account.get("trading_blocked", False),
            "transfers_blocked": account.get("transfers_blocked", False),
            "account_blocked": account.get("account_blocked", False),
            "created_at": account.get("created_at"),
            "trade_suspended_by_user": account.get("trade_suspended_by_user", False),
            "multiplier": float(account.get("multiplier", 1)),
            "shorting_enabled": account.get("shorting_enabled", False),
            "equity_used_for_margin": float(account.get("equity_used_for_margin", 0)),
            "long_market_value": float(account.get("long_market_value", 0)),
            "short_market_value": float(account.get("short_market_value", 0)),
            "initial_margin": float(account.get("initial_margin", 0)),
            "maintenance_margin": float(account.get("maintenance_margin", 0)),
            "last_maintenance_margin": float(account.get("last_maintenance_margin", 0)),
            "sma": float(account.get("sma", 0)),
            "day_trade_buying_power": float(account.get("day_trade_buying_power", 0))
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching account data: {str(e)}")

@app.get("/api/positions")
async def get_positions():
    """Get open positions"""
    try:
        positions = alpaca.get_positions()
        formatted_positions = []
        
        for pos in positions:
            formatted_positions.append({
                "asset_id": pos.get("asset_id"),
                "symbol": pos.get("symbol"),
                "exchange": pos.get("exchange"),
                "asset_class": pos.get("asset_class"),
                "qty": float(pos.get("qty", 0)),
                "side": pos.get("side"),
                "market_value": float(pos.get("market_value", 0)),
                "cost_basis": float(pos.get("cost_basis", 0)),
                "unrealized_pl": float(pos.get("unrealized_pl", 0)),
                "unrealized_plpc": float(pos.get("unrealized_plpc", 0)),
                "unrealized_intraday_pl": float(pos.get("unrealized_intraday_pl", 0)),
                "unrealized_intraday_plpc": float(pos.get("unrealized_intraday_plpc", 0)),
                "current_price": float(pos.get("current_price", 0)),
                "lastday_price": float(pos.get("lastday_price", 0)),
                "change_today": float(pos.get("change_today", 0))
            })
        
        return formatted_positions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching positions: {str(e)}")

@app.get("/api/orders")
async def get_orders(status: str = "all", limit: int = 100):
    """Get order history"""
    try:
        orders = alpaca.get_orders(status=status, limit=limit)
        formatted_orders = []
        
        for order in orders:
            formatted_orders.append({
                "id": order.get("id"),
                "client_order_id": order.get("client_order_id"),
                "created_at": order.get("created_at"),
                "updated_at": order.get("updated_at"),
                "submitted_at": order.get("submitted_at"),
                "filled_at": order.get("filled_at"),
                "expired_at": order.get("expired_at"),
                "canceled_at": order.get("canceled_at"),
                "failed_at": order.get("failed_at"),
                "replaced_at": order.get("replaced_at"),
                "replaced_by": order.get("replaced_by"),
                "replaces": order.get("replaces"),
                "asset_id": order.get("asset_id"),
                "symbol": order.get("symbol"),
                "asset_class": order.get("asset_class"),
                "notional": order.get("notional"),
                "qty": order.get("qty"),
                "filled_qty": order.get("filled_qty"),
                "filled_avg_price": order.get("filled_avg_price"),
                "order_class": order.get("order_class"),
                "order_type": order.get("order_type"),
                "type": order.get("type"),
                "side": order.get("side"),
                "time_in_force": order.get("time_in_force"),
                "limit_price": order.get("limit_price"),
                "stop_price": order.get("stop_price"),
                "status": order.get("status"),
                "extended_hours": order.get("extended_hours"),
                "legs": order.get("legs"),
                "trail_percent": order.get("trail_percent"),
                "trail_price": order.get("trail_price"),
                "hwm": order.get("hwm")
            })
        
        return formatted_orders
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching orders: {str(e)}")

@app.get("/api/activities")
async def get_activities(activity_type: str = "FILL", limit: int = 1000):
    """Get account activities (trades)"""
    try:
        # Get activities with higher limit to ensure we get today's data
        activities = alpaca.get_activities(activity_type=activity_type, limit=limit)
        
        # Filter to today's activities only
        from datetime import datetime, timezone
        today = datetime.now(timezone.utc).date()
        
        filtered_activities = []
        for activity in activities:
            if activity.get('transaction_time'):
                try:
                    # Parse the transaction time
                    transaction_time = datetime.fromisoformat(activity.get('transaction_time').replace('Z', '+00:00'))
                    if transaction_time.date() == today:
                        filtered_activities.append(activity)
                except:
                    # If we can't parse the date, include it anyway
                    filtered_activities.append(activity)
        
        activities = filtered_activities
        formatted_activities = []
        
        for activity in activities:
            formatted_activities.append({
                "id": activity.get("id"),
                "account_id": activity.get("account_id"),
                "activity_type": activity.get("activity_type"),
                "transaction_time": activity.get("transaction_time"),
                "type": activity.get("type"),
                "price": float(activity.get("price", 0)),
                "qty": float(activity.get("qty", 0)),
                "side": activity.get("side"),
                "symbol": activity.get("symbol"),
                "leaves_qty": float(activity.get("leaves_qty", 0)),
                "order_id": activity.get("order_id"),
                "cum_qty": float(activity.get("cum_qty", 0)),
                "date": activity.get("date"),
                "net_amount": float(activity.get("net_amount", 0)),
                "per_share_amount": float(activity.get("per_share_amount", 0))
            })
        
        return formatted_activities
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching activities: {str(e)}")

@app.get("/api/clock")
async def get_clock():
    """Get market clock information"""
    try:
        clock = alpaca.get_clock()
        return {
            "timestamp": clock.get("timestamp"),
            "is_open": clock.get("is_open"),
            "next_open": clock.get("next_open"),
            "next_close": clock.get("next_close")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching clock: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
