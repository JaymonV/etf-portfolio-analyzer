"""Sector allocation analyzer for ETF portfolios."""

import pandas as pd
import time
from pathlib import Path
from ..portfolio import Portfolio
from ..scrapers import SectorScraper


class SectorAnalyzer:
    """Analyzes sector distribution of ETF portfolio."""

    def __init__(self, portfolio: Portfolio, rate_limit: float = 10.0):
        """
        Initialize sector analyzer.

        Args:
            portfolio: Portfolio instance to analyze
            rate_limit: Seconds to wait between requests (default: 10.0)
        """
        self.portfolio = portfolio
        self.rate_limit = rate_limit
        self.sector_distribution: pd.DataFrame = None

    def analyze(self) -> None:
        """Analyze sector distribution of all ETFs in portfolio."""
        print("\nAnalyzing sector distribution from JustETF...")
        print("=" * 120)

        results = []

        with SectorScraper() as scraper:
            for idx, row in self.portfolio.data.iterrows():
                isin = row["ISIN"]
                product = row["Product"]
                value = row["Value_EUR"]

                print(
                    f"\n[{idx}/{self.portfolio.total_positions}] Processing {product[:50]}..."
                )

                sectors = scraper.scrape(isin)
                time.sleep(self.rate_limit)

                if sectors:
                    for sector, percentage in sectors.items():
                        results.append(
                            {
                                "Product": product,
                                "ISIN": isin,
                                "Value_EUR": value,
                                "Sector": sector,
                                "Sector_Percentage": percentage,
                                "Value_in_Sector": value * percentage / 100,
                            }
                        )
                else:
                    results.append(
                        {
                            "Product": product,
                            "ISIN": isin,
                            "Value_EUR": value,
                            "Sector": "Unknown",
                            "Sector_Percentage": 100.0,
                            "Value_in_Sector": value,
                        }
                    )

        self.sector_distribution = pd.DataFrame(results)

    def get_sector_summary(self) -> pd.DataFrame:
        """
        Get sector allocation summary.

        Returns:
            DataFrame with sector allocations and percentages
        """
        if self.sector_distribution is None:
            raise ValueError("Analysis not yet performed. Call analyze() first.")

        summary = (
            self.sector_distribution.groupby("Sector")
            .agg({"Value_in_Sector": "sum"})
            .reset_index()
        )
        summary["Percentage"] = (
            summary["Value_in_Sector"] / self.portfolio.total_value
        ) * 100
        return summary.sort_values("Value_in_Sector", ascending=False)

    def save_results(self) -> None:
        """Save analysis results: raw per-ETF data and dense summaries."""
        if self.sector_distribution is None:
            raise ValueError("Analysis not yet performed. Call analyze() first.")

        raw_path = Path("data/raw")
        out_path = Path("data/output")
        raw_path.mkdir(parents=True, exist_ok=True)
        out_path.mkdir(parents=True, exist_ok=True)

        # Raw: per-ETF sector breakdown
        (
            self.sector_distribution[["ISIN", "Sector", "Sector_Percentage"]]
            .assign(Sector_Percentage=lambda df: df["Sector_Percentage"].round(2))
            .to_csv(raw_path / "sector_distribution.csv", index=False)
        )

        # Output: sector summary (dense)
        sector_summary = self.get_sector_summary()
        sector_summary[["Sector", "Percentage"]].assign(
            Percentage=lambda df: df["Percentage"].round(2)
        ).to_csv(out_path / "sectors.csv", index=False)

        print(f"\nRaw data  → {raw_path}/")
        print(f"Summaries → {out_path}/")
