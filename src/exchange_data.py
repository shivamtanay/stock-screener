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

def truncate_log(msg: str, max_len: int = 100) -> str:
    """Truncate log message to max length."""
    return msg[:max_len] + '...' if len(msg) > max_len else msg

class ExchangeDataCollector:
    def __init__(self):
        # NSE API endpoints
        self.nse_base_url = "https://www.nseindia.com"
        self.nse_pre_open_url = f"{self.nse_base_url}/api/market-data-pre-open?key=ALL"
        self.nse_quote_url = f"{self.nse_base_url}/api/quote-equity"
        
        # Headers for NSE
        self.nse_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
            "Referer": "https://www.nseindia.com/",
            "Origin": "https://www.nseindia.com"
        }
        
        # Initialize NSE session
        self.nse_session = requests.Session()
        self.nse_session.headers.update(self.nse_headers)
        self.api_calls_count = 0  # Track number of API calls made

    def _get_nse_cookies(self):
        """Get required cookies for NSE API."""
        try:
            # First visit the main page to get cookies
            response = self.nse_session.get(self.nse_base_url)
            response.raise_for_status()
            # logger.info(f"Base URL response: {truncate_log(response.text)}")
            time.sleep(1)  # Respect rate limiting
            
            # Get the market data page to get additional cookies
            response = self.nse_session.get(f"{self.nse_base_url}/market-data/live-equity-market")
            response.raise_for_status()
            #logger.info(f"Market data response: {truncate_log(response.text)}")
            time.sleep(1)
            
            return True
        except requests.exceptions.RequestException as e:
            logger.error(truncate_log(f"Cookie fetch failed: {str(e)}"))
            return False

    def get_all_nse_stocks(self) -> List[str]:
        """Get list of all NSE listed stocks."""
        try:
            if not self._get_nse_cookies():
                return []

            response = self.nse_session.get(self.nse_pre_open_url)
            response.raise_for_status()
            
            data = response.json()
            symbols = [item['metadata']['symbol'] for item in data['data'] if item.get('metadata', {}).get('symbol')]
            logger.info(f"Found {len(symbols)} symbols in pre-open market data")
            logger.info("Completed fetching all NSE stocks")
            return symbols
        except Exception as e:
            logger.error(f"Error fetching NSE stocks: {str(e)}")
            return []

    def get_stock_details(self, symbol: str) -> Dict:
        """Get detailed data for a specific stock including market cap."""
        try:
            # Only make 5 API calls
            if self.api_calls_count >= 5:
                logger.info("Reached maximum API call limit (5)")
                return {}

            url = f"{self.nse_quote_url}?symbol={symbol}"
            response = self.nse_session.get(url)
            response.raise_for_status()
            
            self.api_calls_count += 1
            data = response.json()
            logger.info(f"Completed fetching details for {symbol} (API call {self.api_calls_count}/5)")
            return data
        except Exception as e:
            logger.error(f"Error fetching {symbol}: {str(e)}")
            return {}

    def get_market_cap(self, stock_data: Dict) -> float:
        """Extract market cap from stock data in crores."""
        try:
            # Get last price and issued size
            last_price = float(stock_data.get('priceInfo', {}).get('lastPrice', 0))
            issued_size = float(stock_data.get('securityInfo', {}).get('issuedSize', 0))
            
            # Calculate market cap in crores
            market_cap = (last_price * issued_size) / 10000000
            logger.info(f"Completed calculating market cap: {market_cap} crores")
            return market_cap
        except (ValueError, TypeError, KeyError):
            return 0

    def filter_by_market_cap(self, stock_data: Dict, min_cap: float = 100, max_cap: float = 10000) -> bool:
        """Check if stock's market cap is within the specified range."""
        market_cap = self.get_market_cap(stock_data)
        return min_cap <= market_cap <= max_cap

    def get_eligible_stocks(self) -> pd.DataFrame:
        """Get all eligible stocks from NSE based on market cap criteria."""
        # Initialize cookie session
        if not self._get_nse_cookies():
            return pd.DataFrame()

        # Step 1: Get all NSE stocks
        symbols = self.get_all_nse_stocks()
        if not symbols:
            return pd.DataFrame()

        # Step 2: Filter by market cap
        eligible_stocks = []
        
        for symbol in symbols:
            stock_data = self.get_stock_details(symbol)
            if not stock_data:
                continue
                
            if self.filter_by_market_cap(stock_data):
                eligible_stocks.append({
                    'symbol': symbol,
                    'company_name': stock_data.get('info', {}).get('companyName', ''),
                    'market_cap': self.get_market_cap(stock_data),
                    'exchange': 'NSE'
                })
        
        logger.info(f"Found {len(eligible_stocks)} stocks meeting market cap criteria")
        logger.info("Completed fetching eligible stocks")
        return pd.DataFrame(eligible_stocks) 