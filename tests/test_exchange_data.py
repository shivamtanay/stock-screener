import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
from src.exchange_data import ExchangeDataCollector

class TestExchangeDataCollector(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.collector = ExchangeDataCollector()

    @patch('requests.Session')
    def test_get_all_nse_stocks(self, mock_session):
        """Test getting all NSE stocks from pre-open market data."""
        # Mock successful response with sample data matching actual NSE API structure
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "declines": 765,
            "unchanged": 304,
            "data": [
                {
                    "metadata": {
                        "symbol": "SPORTKING",
                        "identifier": "SPORTKINGEQN",
                        "purpose": None,
                        "lastPrice": 103.58,
                        "change": 11.4,
                        "pChange": 12.37,
                        "previousClose": 92.18,
                        "finalQuantity": 15015,
                        "totalTurnover": 1555253,
                        "marketCap": "-",
                        "yearHigh": 159.54,
                        "yearLow": 69.91,
                        "iep": 103.58,
                        "chartTodayPath": "https://nsearchives.nseindia.com/today/preOpen_SPORTKINGEQN.svg"
                    },
                    "detail": {
                        "preOpenMarket": {
                            "preopen": [
                                {"price": 101, "buyQty": 2300, "sellQty": 0},
                                {"price": 101.15, "buyQty": 10, "sellQty": 0},
                                {"price": 101.5, "buyQty": 4000, "sellQty": 0},
                                {"price": 102, "buyQty": 50, "sellQty": 0},
                                {"price": 102.1, "buyQty": 900, "sellQty": 0},
                                {"price": 103.58, "buyQty": 0, "sellQty": 776, "iep": True},
                                {"price": 103.6, "buyQty": 0, "sellQty": 200},
                                {"price": 103.67, "buyQty": 0, "sellQty": 1350},
                                {"price": 103.9, "buyQty": 0, "sellQty": 5000},
                                {"price": 103.99, "buyQty": 0, "sellQty": 25}
                            ],
                            "ato": {"totalBuyQuantity": 0, "totalSellQuantity": 0},
                            "IEP": 103.58,
                            "totalTradedVolume": 15015,
                            "finalPrice": 103.58,
                            "finalQuantity": 15015,
                            "lastUpdateTime": "02-May-2025 09:07:31",
                            "totalSellQuantity": 29336,
                            "totalBuyQuantity": 152767,
                            "atoBuyQty": 0,
                            "atoSellQty": 0,
                            "Change": 11.4,
                            "perChange": 12.37,
                            "prevClose": 92.18
                        }
                    }
                }
            ]
        }
        mock_session.return_value.get.return_value = mock_response

        # Patch the session in the collector
        self.collector.nse_session = mock_session.return_value

        # Mock cookie retrieval to succeed
        with patch.object(self.collector, '_get_nse_cookies', return_value=True):
            result = self.collector.get_all_nse_stocks()
            
            # Verify the result
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0], "SPORTKING")

if __name__ == '__main__':
    unittest.main() 