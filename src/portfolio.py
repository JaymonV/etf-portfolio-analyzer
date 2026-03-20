"""Portfolio data loading and management.

This module provides the Portfolio class for loading and managing ETF portfolio
data from CSV files. It handles data validation, cleaning, and provides summary
statistics.

Typical usage example:
    portfolio = Portfolio('data/Portfolio.csv')
    print(portfolio.summary())
    total = portfolio.total_value
"""

import logging
from pathlib import Path
from typing import Optional

import pandas as pd

# Configure module logger
logger = logging.getLogger(__name__)


class PortfolioError(Exception):
    """Base exception for portfolio-related errors."""

    pass


class PortfolioLoadError(PortfolioError):
    """Exception raised when portfolio cannot be loaded from CSV."""

    pass


class PortfolioValidationError(PortfolioError):
    """Exception raised when portfolio data fails validation."""

    pass


class Portfolio:
    """Manages portfolio data loaded from CSV files.

    This class handles loading, cleaning, and validating portfolio data from
    Degiro CSV exports. Columns are matched by position (0–3), so any language
    export works: Dutch, English, German, French, etc.

    Attributes:
        csv_path: Path to the portfolio CSV file.
        data: DataFrame containing cleaned portfolio data with columns:
            - Product: ETF product name
            - ISIN: ISIN identifier
            - Quantity: Number of shares
            - Value_EUR: Total value in EUR
    """

    # Column indices in the Degiro CSV export (language-agnostic)
    # 0: product name, 1: symbol/ISIN, 2: quantity, 3: close price,
    # 4: local value, 5: currency, 6: value in EUR
    COL_PRODUCT = 0
    COL_ISIN = 1
    COL_QUANTITY = 2
    COL_VALUE = 6
    MIN_COLUMNS = 4

    # Output column names after loading
    OUTPUT_COLUMNS = ['Product', 'ISIN', 'Quantity', 'Value_EUR']

    def __init__(self, csv_path: str = 'data/Portfolio.csv') -> None:
        """Initialize Portfolio with data from CSV file.

        Args:
            csv_path: Path to the portfolio CSV file. Defaults to
                'data/Portfolio.csv'.

        Raises:
            PortfolioLoadError: If the CSV file cannot be read.
            PortfolioValidationError: If the CSV data is invalid.
        """
        self.csv_path = Path(csv_path)
        self.data: Optional[pd.DataFrame] = None
        self._load_portfolio()

    def _load_portfolio(self) -> None:
        """Load and clean portfolio data from CSV file.

        Raises:
            PortfolioLoadError: If the file cannot be read.
            PortfolioValidationError: If the CSV has fewer than 4 columns or
                data is invalid.
        """
        logger.info(f"Loading portfolio from {self.csv_path}")

        # Validate file exists
        if not self.csv_path.exists():
            raise PortfolioLoadError(
                f"Portfolio file not found: {self.csv_path}"
            )

        # Read CSV file
        try:
            df = pd.read_csv(self.csv_path)
        except Exception as e:
            raise PortfolioLoadError(
                f"Failed to read CSV file: {str(e)}"
            ) from e

        # Validate column count (language-agnostic: use positional indexing)
        if len(df.columns) < self.MIN_COLUMNS:
            raise PortfolioValidationError(
                f"Expected at least {self.MIN_COLUMNS} columns, "
                f"got {len(df.columns)}"
            )

        # Extract columns by position and rename to canonical names
        portfolio = df.iloc[:, [self.COL_PRODUCT, self.COL_ISIN,
                                 self.COL_QUANTITY, self.COL_VALUE]].copy()
        portfolio.columns = self.OUTPUT_COLUMNS

        # Clean and validate data
        portfolio = self._clean_dataframe(portfolio)

        # Convert and validate types
        portfolio = self._convert_types(portfolio)

        # Final validation
        if portfolio.empty:
            raise PortfolioValidationError("Portfolio is empty after cleaning")

        self.data = portfolio
        logger.info(
            f"Successfully loaded portfolio with {len(portfolio)} positions"
        )

    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean dataframe by removing invalid rows.

        Args:
            df: Input dataframe to clean.

        Returns:
            Cleaned dataframe.
        """
        initial_count = len(df)

        # Remove rows with missing Product or ISIN
        df = df.dropna(subset=['Product', 'ISIN'])

        # Remove rows where ISIN is not a string (invalid data)
        df = df[df['ISIN'].astype(str).str.len() > 0]

        removed_count = initial_count - len(df)
        if removed_count > 0:
            logger.warning(
                f"Removed {removed_count} invalid rows during cleaning"
            )

        return df

    def _convert_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert columns to appropriate types and handle formatting.

        Args:
            df: Dataframe to convert.

        Returns:
            Dataframe with converted types.

        Raises:
            PortfolioValidationError: If type conversion fails.
        """
        try:
            # Clean and convert Value_EUR (handle quotes and comma decimals)
            df['Value_EUR'] = (
                df['Value_EUR']
                .astype(str)
                .str.replace('"', '', regex=False)
                .str.replace(',', '.', regex=False)
                .astype(float)
            )

            # Convert Quantity to numeric
            df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce')

            # Remove rows with invalid numeric values
            initial_count = len(df)
            df = df.dropna(subset=['Value_EUR', 'Quantity'])
            df = df[df['Value_EUR'] > 0]
            df = df[df['Quantity'] > 0]

            removed_count = initial_count - len(df)
            if removed_count > 0:
                logger.warning(
                    f"Removed {removed_count} rows with invalid numeric values"
                )

            return df

        except Exception as e:
            raise PortfolioValidationError(
                f"Failed to convert data types: {str(e)}"
            ) from e

    @property
    def total_value(self) -> float:
        """Get total portfolio value in EUR.

        Returns:
            Total value of all positions in EUR.
        """
        if self.data is None:
            return 0.0
        return float(self.data['Value_EUR'].sum())

    @property
    def total_positions(self) -> int:
        """Get total number of positions.

        Returns:
            Number of positions in the portfolio.
        """
        if self.data is None:
            return 0
        return len(self.data)

    def summary(self) -> str:
        """Get portfolio summary string.

        Returns:
            Formatted summary string with position count and total value.
        """
        return (
            f"Portfolio Summary:\n"
            f"Total positions: {self.total_positions}\n"
            f"Total value: €{self.total_value:,.2f}"
        )

    def validate(self) -> bool:
        """Validate portfolio data integrity.

        Returns:
            True if portfolio is valid, False otherwise.
        """
        if self.data is None or self.data.empty:
            return False

        # Check for required columns
        required = set(self.OUTPUT_COLUMNS)
        if not required.issubset(set(self.data.columns)):
            return False

        # Check for invalid values
        if (self.data['Value_EUR'] <= 0).any():
            return False
        if (self.data['Quantity'] <= 0).any():
            return False

        return True
