import pytest
import pandas as pd
from src.exchange_data import ExchangeDataCollector
from unittest.mock import patch, MagicMock

@pytest.fixture
def collector():
    return ExchangeDataCollector()

def test_filter_by_market_cap(collector):
    # Create test data
    test_data = pd.DataFrame({
        'market_cap': [50 * 10000000, 100 * 10000000, 5000 * 10000000, 15000 * 10000000],
        'company_name': ['Company A', 'Company B', 'Company C', 'Company D']
    })
    
    # Test filtering
    filtered_data = collector.filter_by_market_cap(test_data)
    
    # Assertions
    assert len(filtered_data) == 2  # Only Company B and C should be included
    assert 'Company B' in filtered_data['company_name'].values
    assert 'Company C' in filtered_data['company_name'].values
    assert 'Company A' not in filtered_data['company_name'].values
    assert 'Company D' not in filtered_data['company_name'].values

def test_handle_dual_listings(collector):
    # Create test data with dual listings
    test_data = pd.DataFrame({
        'company_name': ['Company A', 'Company A', 'Company B', 'Company C'],
        'exchange': ['NSE', 'BSE', 'NSE', 'BSE'],
        'market_cap': [1000 * 10000000] * 4
    })
    
    # Test handling dual listings
    processed_data = collector.handle_dual_listings(test_data)
    
    # Assertions
    assert len(processed_data) == 3  # Should have 3 unique companies
    assert len(processed_data[processed_data['company_name'] == 'Company A']) == 1  # Only one entry for Company A

@patch('src.exchange_data.ExchangeDataCollector.fetch_nse_data')
@patch('src.exchange_data.ExchangeDataCollector.fetch_bse_data')
def test_get_eligible_stocks(mock_fetch_bse, mock_fetch_nse, collector):
    # Mock NSE data
    mock_nse_data = pd.DataFrame({
        'company_name': ['Company A', 'Company B'],
        'market_cap': [5000 * 10000000, 2000 * 10000000],
        'exchange': ['NSE'] * 2
    })
    mock_fetch_nse.return_value = mock_nse_data

    # Mock BSE data
    mock_bse_data = pd.DataFrame({
        'company_name': ['Company C', 'Company D'],
        'market_cap': [3000 * 10000000, 15000 * 10000000],
        'exchange': ['BSE'] * 2
    })
    mock_fetch_bse.return_value = mock_bse_data

    # Get eligible stocks
    result = collector.get_eligible_stocks()
    
    # Assertions
    assert isinstance(result, pd.DataFrame)
    assert not result.empty
    assert 'exchange' in result.columns
    assert 'market_cap' in result.columns
    assert len(result) == 3  # Only 3 companies should be in the range
    assert 'Company D' not in result['company_name'].values  # Company D is above max cap 