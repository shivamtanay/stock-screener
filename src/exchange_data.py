import requests
import pandas as pd
from typing import List, Dict
import logging
from datetime import datetime
import time
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'  # Simplified format
)
logger = logging.getLogger(__name__)

class ExchangeDataCollector:
    def __init__(self):
        # NSE API endpoints
        self.nse_base_url = "https://www.nseindia.com"
        self.nse_pre_open_url = f"{self.nse_base_url}/api/market-data-pre-open?key=ALL"
        
        # Headers for NSE
        self.nse_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "application/json, text/plain, */*",
            "Connection": "keep-alive",
            "Referer": "https://www.nseindia.com/",
            "Origin": "https://www.nseindia.com"
        }
        
        # Initialize NSE session
        self.nse_session = requests.Session()
        self.nse_session.headers.update(self.nse_headers)

    def _get_nse_cookies(self):
        """Get required cookies for NSE API."""
        try:
            # First visit the main page to get cookies
            response = self.nse_session.get(self.nse_base_url)
            response.raise_for_status()
            time.sleep(1)  # Respect rate limiting
            
            # Get the market data page to get additional cookies
            response = self.nse_session.get(f"{self.nse_base_url}/market-data/live-equity-market")
            response.raise_for_status()
            time.sleep(1)
            
            return True
        except requests.exceptions.RequestException:
            return False

    def fetch_nse_data(self) -> pd.DataFrame:
        """Fetch stock data from NSE."""
        try:
            if not self._get_nse_cookies():
                return pd.DataFrame()

            response = self.nse_session.get(self.nse_pre_open_url)
            response.raise_for_status()
            
            data = response.json()
            logger.info(json.dumps(data, indent=2))  # Pretty print the JSON response
            
            # Process the data
            df = pd.DataFrame(data)
            if not df.empty:
                df['exchange'] = 'NSE'
                if 'market_cap' not in df.columns:
                    df['market_cap'] = df.get('marketCap', 0)
                if 'company_name' not in df.columns:
                    df['company_name'] = df.get('symbol', '')
            return df
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return pd.DataFrame()

    def filter_by_market_cap(self, df: pd.DataFrame, min_cap: float = 100, max_cap: float = 10000) -> pd.DataFrame:
        """Filter stocks by market capitalization range (in crores)."""
        try:
            if df.empty:
                return df
            return df[
                (df['market_cap'] >= min_cap * 10000000) &
                (df['market_cap'] <= max_cap * 10000000)
            ]
        except Exception:
            return pd.DataFrame()

    def get_eligible_stocks(self) -> pd.DataFrame:
        """Get all eligible stocks from NSE."""
        nse_data = self.fetch_nse_data()
        return self.filter_by_market_cap(nse_data)

    def handle_dual_listings(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle dual-listed securities by keeping unique entries."""
        if df.empty:
            return df
        return df.drop_duplicates(subset=['company_name'], keep='first') 