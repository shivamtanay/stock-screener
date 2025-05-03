from exchange_data import ExchangeDataCollector
import logging
import sys

def main():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Initialize collector
    collector = ExchangeDataCollector()
    
    # Get eligible stocks
    logging.info("Fetching eligible stocks...")
    eligible_stocks = collector.get_eligible_stocks()
    
    # Handle dual listings
    logging.info("Processing dual listings...")
    final_stocks = collector.handle_dual_listings(eligible_stocks)
    
    # Display results
    if final_stocks.empty:
        logging.warning("No eligible stocks found. This could be due to:")
        logging.warning("1. API access issues (check if you have proper access to NSE/BSE APIs)")
        logging.warning("2. No stocks meeting the market cap criteria")
        logging.warning("3. Network connectivity issues")
        sys.exit(1)
    
    logging.info(f"Found {len(final_stocks)} eligible stocks")
    print("\nEligible Stocks Summary:")
    
    # Check if required columns exist
    required_columns = ['company_name', 'exchange', 'market_cap']
    missing_columns = [col for col in required_columns if col not in final_stocks.columns]
    
    if missing_columns:
        logging.error(f"Missing required columns: {missing_columns}")
        logging.error("Available columns:", final_stocks.columns.tolist())
        sys.exit(1)
    
    # Display the results
    print(final_stocks[required_columns].head())

if __name__ == "__main__":
    main() 