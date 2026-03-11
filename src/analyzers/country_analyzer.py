"""Country allocation analyzer for ETF portfolios."""

import pandas as pd
import time
from pathlib import Path
from typing import Dict, Optional
from ..portfolio import Portfolio
from ..scrapers import CountryScraper


class CountryAnalyzer:
    """Analyzes geographic distribution of ETF portfolio."""

    # Regional groupings
    REGION_MAPPING: Dict[str, str] = {
        "United States": "United States",
        "USA": "United States",
        # Europe
        "United Kingdom": "Europe",
        "UK": "Europe",
        "Germany": "Europe",
        "France": "Europe",
        "Switzerland": "Europe",
        "Netherlands": "Europe",
        "Sweden": "Europe",
        "Denmark": "Europe",
        "Italy": "Europe",
        "Spain": "Europe",
        "Belgium": "Europe",
        "Ireland": "Europe",
        "Norway": "Europe",
        "Finland": "Europe",
        "Austria": "Europe",
        "Portugal": "Europe",
        "Poland": "Europe",
        "Luxembourg": "Europe",
        "Greece": "Europe",
        "Czech Republic": "Europe",
        "Hungary": "Europe",
        "Romania": "Europe",
        # Japan
        "Japan": "Japan",
        # Developed Asia-Pacific (ex-Japan) - South Korea as developed
        "Australia": "Developed Asia-Pacific (ex-Japan)",
        "Singapore": "Developed Asia-Pacific (ex-Japan)",
        "Hong Kong": "Developed Asia-Pacific (ex-Japan)",
        "South Korea": "Developed Asia-Pacific (ex-Japan)",
        "New Zealand": "Developed Asia-Pacific (ex-Japan)",
        # Canada
        "Canada": "Canada",
        # Emerging Markets
        "China": "Emerging Markets",
        "India": "Emerging Markets",
        "Taiwan": "Emerging Markets",
        "Brazil": "Emerging Markets",
        "South Africa": "Emerging Markets",
        "Mexico": "Emerging Markets",
        "Thailand": "Emerging Markets",
        "Malaysia": "Emerging Markets",
        "Indonesia": "Emerging Markets",
        "Philippines": "Emerging Markets",
        "Turkey": "Emerging Markets",
        "Saudi Arabia": "Emerging Markets",
        "UAE": "Emerging Markets",
        "Argentina": "Emerging Markets",
        "Chile": "Emerging Markets",
        "Qatar": "Emerging Markets",
        "Vietnam": "Emerging Markets",
        "Colombia": "Emerging Markets",
        "Peru": "Emerging Markets",
        "Egypt": "Emerging Markets",
        "Morocco": "Emerging Markets",
        "Nigeria": "Emerging Markets",
        "Kenya": "Emerging Markets",
        "Pakistan": "Emerging Markets",
        "Bangladesh": "Emerging Markets",
        "Kazakhstan": "Emerging Markets",
        "Kuwait": "Emerging Markets",
        "Bahrain": "Emerging Markets",
        "Oman": "Emerging Markets",
        "Jordan": "Emerging Markets",
        "Russia": "Emerging Markets",
        # Other
        "Other": "Other",
        "Others": "Other",
        "Rest of World": "Other",
        "Emerging Markets": "Emerging Markets",
        "Unknown": "Unknown",
    }

    def __init__(self, portfolio: Portfolio, rate_limit: float = 10.0):
        """
        Initialize country analyzer.

        Args:
            portfolio: Portfolio instance to analyze
            rate_limit: Seconds to wait between requests (default: 10.0)
        """
        self.portfolio = portfolio
        self.rate_limit = rate_limit
        self.country_distribution: pd.DataFrame = None
        self.regional_distribution: pd.DataFrame = None

    def analyze(self) -> None:
        """Analyze geographic distribution of all ETFs in portfolio."""
        print("\nAnalyzing geographic distribution from JustETF...")
        print("=" * 120)

        results = []

        with CountryScraper() as scraper:
            for idx, row in self.portfolio.data.iterrows():
                isin = row["ISIN"]
                product = row["Product"]
                value = row["Value_EUR"]

                print(
                    f"\n[{idx}/{self.portfolio.total_positions}] Processing {product[:50]}..."
                )

                countries = scraper.scrape(isin)
                time.sleep(self.rate_limit)

                if countries:
                    for country, percentage in countries.items():
                        results.append(
                            {
                                "Product": product,
                                "ISIN": isin,
                                "Value_EUR": value,
                                "Country": country,
                                "Country_Percentage": percentage,
                                "Value_in_Country": value * percentage / 100,
                            }
                        )
                else:
                    results.append(
                        {
                            "Product": product,
                            "ISIN": isin,
                            "Value_EUR": value,
                            "Country": "Unknown",
                            "Country_Percentage": 100.0,
                            "Value_in_Country": value,
                        }
                    )

        self.country_distribution = pd.DataFrame(results)
        self._calculate_regional_distribution()

    def _calculate_regional_distribution(self) -> None:
        """Calculate regional groupings from country data."""
        # Map countries to regions
        self.country_distribution["Region"] = (
            self.country_distribution["Country"]
            .map(self.REGION_MAPPING)
            .fillna("Other")
        )

        # Calculate regional allocation
        self.regional_distribution = (
            self.country_distribution.groupby("Region")
            .agg({"Value_in_Country": "sum"})
            .reset_index()
        )
        self.regional_distribution.columns = ["Region", "Value_in_Region"]
        self.regional_distribution["Percentage"] = (
            self.regional_distribution["Value_in_Region"] / self.portfolio.total_value
        ) * 100
        self.regional_distribution = self.regional_distribution.sort_values(
            "Value_in_Region", ascending=False
        )

    def get_country_summary(self) -> pd.DataFrame:
        """
        Get country allocation summary.

        Returns:
            DataFrame with country allocations and percentages
        """
        if self.country_distribution is None:
            raise ValueError("Analysis not yet performed. Call analyze() first.")

        summary = (
            self.country_distribution.groupby("Country")
            .agg({"Value_in_Country": "sum"})
            .reset_index()
        )
        summary["Percentage"] = (
            summary["Value_in_Country"] / self.portfolio.total_value
        ) * 100
        return summary.sort_values("Value_in_Country", ascending=False)

    def get_regional_summary(self) -> pd.DataFrame:
        """
        Get regional allocation summary.

        Returns:
            DataFrame with regional allocations and percentages
        """
        if self.regional_distribution is None:
            raise ValueError("Analysis not yet performed. Call analyze() first.")

        return self.regional_distribution

    def save_results(self) -> None:
        """Save analysis results: raw per-ETF data and dense summaries."""
        if self.country_distribution is None:
            raise ValueError("Analysis not yet performed. Call analyze() first.")

        raw_path = Path("data/raw")
        out_path = Path("data/output")
        raw_path.mkdir(parents=True, exist_ok=True)
        out_path.mkdir(parents=True, exist_ok=True)

        # Raw: per-ETF country breakdown
        (
            self.country_distribution[["ISIN", "Country", "Country_Percentage"]]
            .assign(Country_Percentage=lambda df: df["Country_Percentage"].round(2))
            .to_csv(raw_path / "country_distribution.csv", index=False)
        )

        # Output: country summary (dense)
        country_summary = self.get_country_summary()
        country_summary[["Country", "Percentage"]].assign(
            Percentage=lambda df: df["Percentage"].round(2)
        ).to_csv(out_path / "countries.csv", index=False)

        # Output: regional summary (dense)
        regional_summary = self.get_regional_summary()
        regional_summary[["Region", "Percentage"]].assign(
            Percentage=lambda df: df["Percentage"].round(2)
        ).to_csv(out_path / "regions.csv", index=False)

        print(f"\nRaw data  → {raw_path}/")
        print(f"Summaries → {out_path}/")
