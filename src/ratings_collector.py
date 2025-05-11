import os
import logging
from datetime import datetime
import time
from stock_ratings import StockRatingsAnalyzer
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)

class RatingsCollector:
    def __init__(self):
        self.ratings_analyzer = StockRatingsAnalyzer()
        self.ratings_file = "ratings.txt"
        
    def _is_stock_rated(self, symbol: str) -> bool:
        """Check if ratings for the stock are already present in ratings.txt."""
        if not os.path.exists(self.ratings_file):
            return False
            
        try:
            with open(self.ratings_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Look for "Stock: SYMBOL" pattern
                return f"Stock: {symbol}" in content
        except Exception as e:
            logger.error(f"Error checking ratings for {symbol}: {str(e)}")
            return False

    def save_ratings(self, symbol: str, content: dict) -> None:
        """Save ratings content to a text file."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(self.ratings_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"Stock: {symbol}\n")
            f.write(f"Timestamp: {timestamp}\n")
            f.write(f"Company Name: {content['metadata']['company_name']}\n")
            f.write(f"Market Cap: {content['metadata']['market_cap']}\n")
            f.write(f"Rating Link: {content['metadata']['rating_link']}\n")
            f.write(f"{'-'*80}\n")
            
            if content.get('page_text'):
                f.write("\nPage Text:\n")
                f.write(content['page_text'])
                f.write("\n")
            
            if content.get('pdf_text'):
                f.write("\nPDF Text:\n")
                f.write(content['pdf_text'])
                f.write("\n")
            
            f.write(f"{'='*80}\n")
            
        logger.info(f"Added ratings for {symbol} to {self.ratings_file}")

    def collect_ratings(self, eligible_stocks: pd.DataFrame) -> None:
        """
        Collect and store ratings for each eligible stock.
        
        Args:
            eligible_stocks (pd.DataFrame): DataFrame containing eligible stocks
        """
        if eligible_stocks.empty:
            logger.error("No eligible stocks provided")
            return
            
        logger.info(f"\nStarting to collect ratings for {len(eligible_stocks)} stocks...")
        
        for _, stock in eligible_stocks.iterrows():
            symbol = stock['symbol']
            logger.info(f"\nProcessing {symbol}...")
            
            # Check if ratings already exist
            if self._is_stock_rated(symbol):
                logger.info(f"Ratings for {symbol} already exist, skipping...")
                continue
            
            # Get credit ratings link
            rating_link = self.ratings_analyzer.get_credit_ratings_link(symbol)
            if not rating_link:
                logger.warning(f"No credit ratings found for {symbol}")
                continue
            
            # Get rating content
            content = self.ratings_analyzer.get_rating_page_text(rating_link)
            if not content:
                logger.warning(f"Could not fetch content for {symbol}")
                continue
            
            # Add metadata
            content['metadata'] = {
                'symbol': symbol,
                'company_name': stock['company_name'],
                'market_cap': stock['market_cap'],
                'rating_link': rating_link,
                'timestamp': datetime.now().isoformat()
            }
            
            # Save to file
            self.save_ratings(symbol, content)
            
            # Add a small delay to avoid overwhelming the server
            time.sleep(2)
            
        logger.info("\nCompleted collecting ratings for all stocks") 