# Stock Ratings Analyzer

A Python tool to collect and analyze credit ratings for Indian stocks, with a focus on revenue growth projections.

## Features

- Collects credit ratings from major rating agencies (ICRA, CARE, CRISIL)
- Extracts and analyzes revenue growth projections
- Caches stock data to minimize API calls
- Uses Perplexity AI for intelligent analysis of rating documents
- Maintains analysis history in a single file

## Prerequisites

- Python 3.8 or higher
- Perplexity API key
- Internet connection for fetching ratings

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/stocks-suggestion.git
cd stocks-suggestion
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root:
```
PERPLEXITY_TOKEN=your_perplexity_api_key
```

## Project Structure

```
stocks-suggestion/
├── src/
│   ├── exchange_data.py      # Stock data collection
│   ├── stock_ratings.py      # Rating document fetching
│   ├── ratings_collector.py  # Rating collection and storage
│   └── analyze_ratings.py    # Growth projection analysis
├── tests/
│   ├── test_exchange_data.py
│   └── test_ratings_collector.py
├── requirements.txt
├── .env
└── README.md
```

## Usage

1. Collect eligible stocks:
```bash
python src/main.py
```

2. Analyze ratings for growth projections:
```bash
python src/analyze_ratings.py
```

## Output Files

- `ratings.txt`: Contains collected rating documents
- `growth_analysis.txt`: Contains analyzed growth projections
- `stock_details_cache.json`: Cached stock data
- `stock_symbols_cache.json`: Cached stock symbols

## Caching

The system implements caching at multiple levels:
- Stock symbols are cached to avoid repeated API calls
- Stock details are cached for 2 days
- Rating analysis is stored in a single file to avoid reprocessing

## Testing

Run tests using pytest:
```bash
pytest tests/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- NSE India for stock data
- Rating agencies (ICRA, CARE, CRISIL) for rating documents
- Perplexity AI for analysis capabilities
