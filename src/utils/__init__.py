from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import pandas as pd
from datetime import datetime
import time

class BaseExchange(ABC):
    """Base class for stock exchange data fetching"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        }
        self.last_request_time = 0
        self.min_request_interval = 1
        
        # Market cap filter constants (in Crores)
        self.MIN_MARKET_CAP = 100
        self.MAX_MARKET_CAP = 10000
    
    def _rate_limit(self):
        """Implements rate limiting for API requests"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last_request)
        self.last_request_time = time.time()
    
    def filter_by_market_cap(self, stocks_df: pd.DataFrame) -> pd.DataFrame:
        """Filter stocks by market cap range (₹100-10,000 Cr)"""
        return stocks_df[
            (stocks_df['market_cap'] >= self.MIN_MARKET_CAP) &
            (stocks_df['market_cap'] <= self.MAX_MARKET_CAP)
        ]
    
    @abstractmethod
    def get_all_stocks(self) -> Optional[pd.DataFrame]:
        """Fetch all stocks from exchange"""
        pass
    
    @abstractmethod
    def get_stock_details(self, symbol: str) -> Optional[Dict]:
        """Fetch details for a specific stock"""
        pass
