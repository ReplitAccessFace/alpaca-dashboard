import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from config import ALPACA_KEY, ALPACA_SECRET, ALPACA_BASE_URL

class AlpacaClient:
    def __init__(self):
        self.base_url = ALPACA_BASE_URL
        self.headers = {
            'APCA-API-KEY-ID': ALPACA_KEY,
            'APCA-API-SECRET-KEY': ALPACA_SECRET
        }
    
    def get_account(self) -> Dict:
        """Get account information"""
        response = requests.get(f"{self.base_url}/account", headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_positions(self) -> List[Dict]:
        """Get open positions"""
        response = requests.get(f"{self.base_url}/positions", headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_orders(self, status: str = "all", limit: int = 100) -> List[Dict]:
        """Get order history"""
        params = {
            'status': status,
            'limit': limit,
            'direction': 'desc'
        }
        response = requests.get(f"{self.base_url}/orders", headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_activities(self, activity_type: str = "FILL", limit: int = 100) -> List[Dict]:
        """Get account activities (trades)"""
        params = {
            'activity_type': activity_type,
            'limit': limit
        }
        response = requests.get(f"{self.base_url}/account/activities", headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_portfolio_history(self, period: str = "1M", timeframe: str = "1Day") -> Dict:
        """Get portfolio performance history"""
        params = {
            'period': period,
            'timeframe': timeframe
        }
        response = requests.get(f"{self.base_url}/account/portfolio/history", headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_clock(self) -> Dict:
        """Get market clock information"""
        response = requests.get(f"{self.base_url}/clock", headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_bars(self, symbol: str, timeframe: str = "1Day", start: str = None, end: str = None, limit: int = 100) -> List[Dict]:
        """Get historical bars for a symbol"""
        params = {
            'symbols': symbol,
            'timeframe': timeframe,
            'limit': limit
        }
        if start:
            params['start'] = start
        if end:
            params['end'] = end
            
        response = requests.get(f"{self.base_url}/bars", headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

