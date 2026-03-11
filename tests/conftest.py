"""Pytest configuration and fixtures for Portfolio Rebalancer tests."""

import pytest
from pathlib import Path


@pytest.fixture
def test_data_dir():
    """Return path to test data directory."""
    return Path(__file__).parent / "data"


@pytest.fixture
def sample_portfolio_csv(tmp_path):
    """Create a sample portfolio CSV file for testing (Dutch / Degiro NL)."""
    csv_content = """Product,Symbool/ISIN,Aantal,Waarde in EUR
VANGUARD FTSE ALL-WORLD,IE00BK5BQT80,51,"3001.22"
ISHARES MSCI WORLD SRI,IE00BYX2JD69,260,"2800.16"
"""
    csv_file = tmp_path / "test_portfolio.csv"
    csv_file.write_text(csv_content)
    return csv_file


@pytest.fixture
def english_portfolio_csv(tmp_path):
    """Create a sample portfolio CSV file in English (Degiro EN)."""
    csv_content = """Product,Symbol/ISIN,Amount,Value in EUR
VANGUARD FTSE ALL-WORLD,IE00BK5BQT80,51,"3001.22"
ISHARES MSCI WORLD SRI,IE00BYX2JD69,260,"2800.16"
"""
    csv_file = tmp_path / "test_portfolio_en.csv"
    csv_file.write_text(csv_content)
    return csv_file


@pytest.fixture
def invalid_portfolio_csv(tmp_path):
    """Create a CSV with too few columns to trigger validation error."""
    csv_content = """Only,Three,Columns
Value1,Value2,Value3
"""
    csv_file = tmp_path / "invalid_portfolio.csv"
    csv_file.write_text(csv_content)
    return csv_file
