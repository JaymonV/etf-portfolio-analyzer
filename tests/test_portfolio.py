"""Tests for portfolio.py module."""

import pytest
from pathlib import Path

from src.portfolio import (
    Portfolio,
    PortfolioError,
    PortfolioLoadError,
    PortfolioValidationError,
)


class TestPortfolio:
    """Test cases for Portfolio class."""

    def test_load_valid_portfolio(self, sample_portfolio_csv):
        """Test loading a valid portfolio CSV file."""
        portfolio = Portfolio(str(sample_portfolio_csv))

        assert portfolio.total_positions == 2
        assert portfolio.total_value > 0
        assert portfolio.data is not None
        assert len(portfolio.data) == 2

    def test_load_nonexistent_file(self):
        """Test that loading a non-existent file raises PortfolioLoadError."""
        with pytest.raises(PortfolioLoadError, match="Portfolio file not found"):
            Portfolio("nonexistent_file.csv")

    def test_load_english_portfolio(self, english_portfolio_csv):
        """Test loading an English-language Degiro CSV export."""
        portfolio = Portfolio(str(english_portfolio_csv))
        assert portfolio.total_positions == 2
        assert portfolio.total_value > 0

    def test_load_invalid_columns(self, invalid_portfolio_csv):
        """Test that a CSV with fewer than 4 columns raises PortfolioValidationError."""
        with pytest.raises(
            PortfolioValidationError, match="Expected at least 4 columns"
        ):
            Portfolio(str(invalid_portfolio_csv))

    def test_portfolio_summary(self, sample_portfolio_csv):
        """Test portfolio summary generation."""
        portfolio = Portfolio(str(sample_portfolio_csv))
        summary = portfolio.summary()

        assert "Portfolio Summary" in summary
        assert "Total positions: 2" in summary
        assert "Total value" in summary
        assert "€" in summary

    def test_portfolio_validate(self, sample_portfolio_csv):
        """Test portfolio validation."""
        portfolio = Portfolio(str(sample_portfolio_csv))
        assert portfolio.validate() is True

    def test_portfolio_properties(self, sample_portfolio_csv):
        """Test portfolio properties."""
        portfolio = Portfolio(str(sample_portfolio_csv))

        # Check total_value is a float and positive
        assert isinstance(portfolio.total_value, float)
        assert portfolio.total_value > 0

        # Check total_positions is an int and matches row count
        assert isinstance(portfolio.total_positions, int)
        assert portfolio.total_positions == 2

    def test_empty_portfolio_validation(self, tmp_path):
        """Test that empty portfolio fails validation."""
        csv_file = tmp_path / "empty.csv"
        csv_file.write_text("Product,Symbol/ISIN,Amount,Value in EUR\n")

        with pytest.raises(PortfolioValidationError, match="empty after cleaning"):
            Portfolio(str(csv_file))
