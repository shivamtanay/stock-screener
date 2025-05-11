import requests
import pandas as pd
from typing import List, Dict
import logging
from datetime import datetime, timedelta
import time
import json
import os
import shutil
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
        
        # Single cache file for all stock details
        self.cache_file = "stock_details_cache.json"
        self._cleanup_old_cache()

    def _cleanup_old_cache(self) -> None:
        """Clean up old cache files and directory."""
        try:
            # Remove old cache directory if it exists
            if os.path.exists("stock_cache"):
                shutil.rmtree("stock_cache")
                logger.info("Cleaned up old cache directory")
        except Exception as e:
            logger.error(f"Error cleaning up old cache: {str(e)}")

    def _is_cache_valid(self) -> bool:
        """Check if the cache file exists and is not expired."""
        if not os.path.exists(self.cache_file):
            return False
            
        try:
            # Check file modification time
            file_time = datetime.fromtimestamp(os.path.getmtime(self.cache_file))
            if datetime.now() - file_time > timedelta(days=2):
                return False
            return True
        except Exception as e:
            logger.error(f"Error checking cache validity: {str(e)}")
            return False

    def _save_to_cache(self, symbol: str, data: Dict) -> None:
        """Save stock data to cache."""
        try:
            cache_data = {}
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    cache_data = json.load(f)
            
            cache_data[symbol] = {
                'timestamp': datetime.now().isoformat(),
                'data': data
            }
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f)
            logger.info(f"Saved {symbol} details to cache")
        except Exception as e:
            logger.error(f"Error saving to cache: {str(e)}")

    def _get_from_cache(self, symbol: str) -> Dict:
        """Get stock data from cache."""
        try:
            if not os.path.exists(self.cache_file):
                return {}
                
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)
                
            stock_cache = cache_data.get(symbol, {})
            if not stock_cache:
                return {}
                
            # Check if this specific stock's cache is valid
            cache_time = datetime.fromisoformat(stock_cache['timestamp'])
            if datetime.now() - cache_time > timedelta(days=2):
                return {}
                
            return stock_cache['data']
        except Exception as e:
            logger.error(f"Error reading from cache: {str(e)}")
            return {}

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
            # Check cache first
            cached_data = self._get_from_cache(symbol)
            if cached_data:
                logger.info(f"Retrieved {symbol} details from cache")
                return cached_data

            # Only make 100 API calls
            if self.api_calls_count >= 2:
                logger.info("Reached maximum API call limit (2)")
                return {}

            url = f"{self.nse_quote_url}?symbol={symbol}"
            response = self.nse_session.get(url)
            response.raise_for_status()
            
            self.api_calls_count += 1
            data = response.json()
            
            # Save to cache
            self._save_to_cache(symbol, data)
            
            logger.info(f"Completed fetching details for {symbol} (API call {self.api_calls_count}/100)")
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