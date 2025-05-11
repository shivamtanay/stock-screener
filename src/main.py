from exchange_data import ExchangeDataCollector
from ratings_collector import RatingsCollector
import logging
import sys

def main():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s'  # Simplified format
    )
    logger = logging.getLogger(__name__)
    
    # Initialize collectors
    collector = ExchangeDataCollector()
    ratings_collector = RatingsCollector()
    
    # Get eligible stocks
    logger.info("Fetching eligible stocks...")
    eligible_stocks = collector.get_eligible_stocks()
    
    # Display results
    if eligible_stocks.empty:
        logger.warning("No eligible stocks found. This could be due to:")
        logger.warning("1. API access issues (check if you have proper access to NSE/BSE APIs)")
        logger.warning("2. No stocks meeting the market cap criteria")
        logger.warning("3. Network connectivity issues")
        sys.exit(1)
    
    logger.info(f"Found {len(eligible_stocks)} eligible stocks")
    logger.info(f"Eligible stocks data: {eligible_stocks.head().to_string()}")
    print("\nEligible Stocks Summary:")
    
    # Check if required columns exist
    required_columns = ['company_name', 'exchange', 'market_cap']
    missing_columns = [col for col in required_columns if col not in eligible_stocks.columns]
    
    if missing_columns:
        logger.error(f"Missing required columns: {missing_columns}")
        logger.error("Available columns:", eligible_stocks.columns.tolist())
        sys.exit(1)
    
    # Display the results
    print(eligible_stocks[required_columns].head())
    
    # Collect ratings for all eligible stocks
    ratings_collector.collect_ratings(eligible_stocks)

if __name__ == "__main__":
    main() 