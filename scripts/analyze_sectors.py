#!/usr/bin/env python3
"""
Analyze sector distribution of ETF portfolio.

This script loads a portfolio from CSV and analyzes the sector distribution
by scraping data from JustETF. Results include detailed sector allocations.
"""

import json
from pathlib import Path

import pandas as pd
from src.portfolio import Portfolio
from src.analyzers import SectorAnalyzer

TARGETS_PATH = Path("data/input/targets.json")


def load_sector_targets() -> dict:
    if not TARGETS_PATH.exists():
        return {}
    with open(TARGETS_PATH) as f:
        return json.load(f).get("sectors", {})


def main():
    """Main entry point for sector analysis."""
    # Configure pandas display
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', 50)

    # Load portfolio
    print("\n" + "=" * 120)
    print("PORTFOLIO SECTOR ANALYSIS")
    print("=" * 120)

    portfolio = Portfolio('data/Portfolio.csv')
    print(f"\n{portfolio.summary()}\n")

    # Display portfolio
    print("\nPortfolio Holdings:")
    print("=" * 120)
    print(portfolio.data[['Product', 'ISIN', 'Quantity', 'Value_EUR']])

    # Analyze sector distribution
    analyzer = SectorAnalyzer(portfolio, rate_limit=10.0)
    analyzer.analyze()

    # Display sector summary
    print("\n\nTotal Portfolio Allocation by Sector:")
    print("=" * 120)
    print(analyzer.get_sector_summary().to_string(index=False))

    # Display target vs actual comparison
    targets = load_sector_targets()
    if targets:
        sectors = analyzer.get_sector_summary()[["Sector", "Percentage"]]
        target_df = pd.DataFrame(targets.items(), columns=["Sector", "Target"])
        comparison = sectors.merge(target_df, on="Sector", how="outer").fillna(0)
        comparison["Delta"] = comparison["Percentage"] - comparison["Target"]
        comparison = comparison.sort_values("Delta")
        comparison = comparison.rename(columns={"Percentage": "Actual"})
        comparison[["Actual", "Target", "Delta"]] = comparison[["Actual", "Target", "Delta"]].round(2)
        print("\n\nSector vs Target (positive delta = overweight):")
        print("=" * 120)
        print(comparison[["Sector", "Actual", "Target", "Delta"]].to_string(index=False))

    # Save results
    analyzer.save_results()

    print("\n" + "=" * 120)
    print("ANALYSIS COMPLETE")
    print("=" * 120)


if __name__ == "__main__":
    main()
