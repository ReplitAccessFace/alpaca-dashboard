# Add health check endpoint to existing main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from datetime import datetime
import sqlite3
from performance_api import performance_router
from config import ALPACA_KEY, ALPACA_SECRET, ALPACA_BASE_URL

app = FastAPI(
    title="Alpaca Trading Dashboard API",
    description="API for the Alpaca Trading Dashboard",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include performance router
app.include_router(performance_router, prefix="/api/performance")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Check database connectivity
        db_path = os.path.join(os.path.dirname(__file__), 'trades.db')
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM orders LIMIT 1")
            conn.close()
            db_status = "healthy"
        else:
            db_status = "no_database"
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": db_status,
            "version": "1.0.0"
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "version": "1.0.0"
            }
        )

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Alpaca Trading Dashboard API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

# Existing endpoints from your current main.py
@app.get("/api/account")
async def get_account():
    """Get account information from Alpaca"""
    try:
        import requests
        
        headers = {
            "APCA-API-KEY-ID": ALPACA_KEY,
            "APCA-API-SECRET-KEY": ALPACA_SECRET
        }
        
        response = requests.get(f"{ALPACA_BASE_URL}/v2/account", headers=headers)
        response.raise_for_status()
        
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching account: {str(e)}")

@app.get("/api/positions")
async def get_positions():
    """Get current positions from Alpaca"""
    try:
        import requests
        
        headers = {
            "APCA-API-KEY-ID": ALPACA_KEY,
            "APCA-API-SECRET-KEY": ALPACA_SECRET
        }
        
        response = requests.get(f"{ALPACA_BASE_URL}/v2/positions", headers=headers)
        response.raise_for_status()
        
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching positions: {str(e)}")

@app.get("/api/activities")
async def get_activities(date: str = None):
    """Get account activities from Alpaca"""
    try:
        import requests
        from datetime import datetime
        
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        headers = {
            "APCA-API-KEY-ID": ALPACA_KEY,
            "APCA-API-SECRET-KEY": ALPACA_SECRET
        }
        
        params = {
            "activity_types": "FILL",
            "date": date
        }
        
        response = requests.get(f"{ALPACA_BASE_URL}/v2/account/activities", headers=headers, params=params)
        response.raise_for_status()
        
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching activities: {str(e)}")

@app.get("/api/activities/db")
async def get_activities_from_db(date: str = None):
    """Get activities from local database with date filtering"""
    try:
        if not date:
            from datetime import datetime
            date = datetime.now().strftime('%Y-%m-%d')
        
        # Parse the date to handle various formats
        try:
            # Try parsing as YYYY-MM-DD first
            parsed_date = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            try:
                # Try parsing as ISO format
                parsed_date = datetime.fromisoformat(date.replace('Z', '+00:00')).date()
            except ValueError:
                # Try parsing as DD/MM/YYYY
                parsed_date = datetime.strptime(date, '%d/%m/%Y').date()
        
        # Get activities from the database
        db_path = os.path.join(os.path.dirname(__file__), 'trades.db')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Query activities table for the specified date
        cursor.execute('''
            SELECT * FROM activities 
            WHERE date(transaction_time) = ? 
            ORDER BY transaction_time ASC
        ''', (parsed_date.strftime('%Y-%m-%d'),))
        
        activities = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return activities
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching activities from database: {str(e)}")

@app.get("/api/orders/db")
async def get_orders_from_db(date: str = None):
    """Get orders from local database with date filtering"""
    try:
        if not date:
            from datetime import datetime
            date = datetime.now().strftime('%Y-%m-%d')
        
        # Parse the date to handle various formats
        try:
            # Try parsing as YYYY-MM-DD first
            parsed_date = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            try:
                # Try parsing as ISO format
                parsed_date = datetime.fromisoformat(date.replace('Z', '+00:00')).date()
            except ValueError:
                # Try parsing as DD/MM/YYYY
                parsed_date = datetime.strptime(date, '%d/%m/%Y').date()
        
        # Get orders from the database
        db_path = os.path.join(os.path.dirname(__file__), 'trades.db')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Query orders table for the specified date
        cursor.execute('''
            SELECT * FROM orders 
            WHERE date(created_at) = ? 
            ORDER BY created_at ASC
        ''', (parsed_date.strftime('%Y-%m-%d'),))
        
        orders = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return orders
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching orders from database: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)