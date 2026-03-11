#!/usr/bin/env python3
"""
Analyze geographic (country/regional) distribution of ETF portfolio.

This script loads a portfolio from CSV and analyzes the geographic distribution
by scraping data from JustETF. Results include country-level and regional summaries.
"""

import json
from pathlib import Path

import pandas as pd
from src.portfolio import Portfolio
from src.analyzers import CountryAnalyzer

TARGETS_PATH = Path("data/input/targets.json")


def load_region_targets() -> dict:
    if not TARGETS_PATH.exists():
        return {}
    with open(TARGETS_PATH) as f:
        return json.load(f).get("regions", {})


def main():
    """Main entry point for country analysis."""
    # Configure pandas display
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', 50)

    # Load portfolio
    print("\n" + "=" * 120)
    print("PORTFOLIO GEOGRAPHIC ANALYSIS")
    print("=" * 120)

    portfolio = Portfolio('data/Portfolio.csv')
    print(f"\n{portfolio.summary()}\n")

    # Display portfolio
    print("\nPortfolio Holdings:")
    print("=" * 120)
    print(portfolio.data[['Product', 'ISIN', 'Quantity', 'Value_EUR']])

    # Analyze geographic distribution
    analyzer = CountryAnalyzer(portfolio, rate_limit=10.0)
    analyzer.analyze()

    # Display country summary
    print("\n\nTotal Portfolio Allocation by Country:")
    print("=" * 120)
    print(analyzer.get_country_summary().to_string(index=False))

    # Display regional summary
    print("\n\nTotal Portfolio Allocation by Region:")
    print("=" * 120)
    print(analyzer.get_regional_summary().to_string(index=False))

    # Display target vs actual comparison
    targets = load_region_targets()
    if targets:
        regional = analyzer.get_regional_summary()[["Region", "Percentage"]]
        target_df = pd.DataFrame(targets.items(), columns=["Region", "Target"])
        comparison = regional.merge(target_df, on="Region", how="outer").fillna(0)
        comparison["Delta"] = comparison["Percentage"] - comparison["Target"]
        comparison = comparison.sort_values("Delta")
        comparison = comparison.rename(columns={"Percentage": "Actual"})
        comparison[["Actual", "Target", "Delta"]] = comparison[["Actual", "Target", "Delta"]].round(2)
        print("\n\nRegion vs Target (positive delta = overweight):")
        print("=" * 120)
        print(comparison[["Region", "Actual", "Target", "Delta"]].to_string(index=False))

    # Save results
    analyzer.save_results()

    print("\n" + "=" * 120)
    print("ANALYSIS COMPLETE")
    print("=" * 120)


if __name__ == "__main__":
    main()
