"""Scraper for sector allocation data from JustETF."""

from typing import Dict, Optional, Set
from bs4 import BeautifulSoup
from .base import JustETFScraper


class SectorScraper(JustETFScraper):
    """Scrapes sector allocation data from JustETF."""

    # Valid sector names to filter results
    VALID_SECTORS: Set[str] = {
        'Technology', 'Financials', 'Consumer Discretionary',
        'Industrials', 'Consumer Staples', 'Energy', 'Materials', 'Real Estate',
        'Utilities', 'Communication Services', 'Telecommunication',
        'Basic Materials', 'Consumer Cyclical', 'Consumer Defensive',
        'Health Care', 'Information Technology', 'Financial Services',
        'Telecom', 'Communication', 'Healthcare', 'Industrial', 'Other', 'Others'
    }

    def scrape(self, isin: str) -> Optional[Dict[str, float]]:
        """
        Scrape sector allocation data for a given ISIN.

        Args:
            isin: ISIN code of the ETF

        Returns:
            Dictionary mapping sector names to percentage allocations,
            or None if no data found
        """
        url = f"https://www.justetf.com/en/etf-profile.html?isin={isin}"
        print(f"  Fetching from JustETF: {url}")

        try:
            # Load page
            soup = self._get_page(url)

            # Click 'show more' button for sectors
            self._click_show_more('etf-holdings_sectors_load-more_link')

            # Get updated page source after clicking (don't reload the page!)
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')

            # Find sectors table
            sectors_table = soup.find('table', {'data-testid': 'etf-holdings_sectors_table'})

            if not sectors_table:
                print(f"  Sectors table not found")
                return None

            print(f"  Found sectors table")
            sectors = {}

            # Extract sector data
            rows = sectors_table.find_all('tr', {'data-testid': 'etf-holdings_sectors_row'})

            for row in rows:
                sector_td = row.find('td', {'data-testid': 'tl_etf-holdings_sectors_value_name'})
                percentage_span = row.find('span', {'data-testid': 'tl_etf-holdings_sectors_value_percentage'})

                if sector_td and percentage_span:
                    sector_text = sector_td.get_text(strip=True)
                    percentage_text = percentage_span.get_text(strip=True)

                    try:
                        percentage = float(percentage_text.replace('%', '').strip())

                        # Validate percentage and sector name
                        if 0 < percentage <= 100 and sector_text in self.VALID_SECTORS:
                            sectors[sector_text] = percentage
                    except ValueError:
                        continue

            if sectors:
                print(f"  ✓ Found {len(sectors)} sectors: {list(sectors.keys())}")
                return sectors
            else:
                print(f"  ✗ No sector data found")
                return None

        except Exception as e:
            print(f"  ✗ Error: {e}")
            return None
