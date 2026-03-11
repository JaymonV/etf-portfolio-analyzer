"""Scraper for country allocation data from JustETF."""

from typing import Dict, Optional, Set
from bs4 import BeautifulSoup
from .base import JustETFScraper


class CountryScraper(JustETFScraper):
    """Scrapes country allocation data from JustETF."""

    # Valid country names to filter results
    VALID_COUNTRIES: Set[str] = {
        'United States', 'USA', 'China', 'Japan', 'United Kingdom', 'UK', 'France',
        'Germany', 'Canada', 'Switzerland', 'Australia', 'South Korea', 'Taiwan',
        'Netherlands', 'Sweden', 'Denmark', 'Italy', 'Spain', 'Hong Kong', 'Singapore',
        'India', 'Brazil', 'Mexico', 'Belgium', 'Ireland', 'Norway', 'Finland',
        'Austria', 'Israel', 'New Zealand', 'Portugal', 'Poland', 'Russia', 'Thailand',
        'Malaysia', 'Indonesia', 'Philippines', 'South Africa', 'Turkey', 'Saudi Arabia',
        'UAE', 'Argentina', 'Chile', 'Luxembourg', 'Greece', 'Czech Republic', 'Qatar',
        'Other', 'Others', 'Rest of World', 'Emerging Markets', 'Vietnam', 'Colombia',
        'Peru', 'Hungary', 'Romania', 'Egypt', 'Morocco', 'Nigeria', 'Kenya', 'Pakistan',
        'Bangladesh', 'Kazakhstan', 'Kuwait', 'Bahrain', 'Oman', 'Jordan'
    }

    def scrape(self, isin: str) -> Optional[Dict[str, float]]:
        """
        Scrape country allocation data for a given ISIN.

        Args:
            isin: ISIN code of the ETF

        Returns:
            Dictionary mapping country names to percentage allocations,
            or None if no data found
        """
        url = f"https://www.justetf.com/en/etf-profile.html?isin={isin}"
        print(f"  Fetching from JustETF: {url}")

        try:
            # Load page
            soup = self._get_page(url)

            # Click 'show more' button for countries
            self._click_show_more('etf-holdings_countries_load-more_link')

            # Get updated page source after clicking (don't reload the page!)
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')

            # Find countries table
            countries_table = soup.find('table', {'data-testid': 'etf-holdings_countries_table'})

            if not countries_table:
                print(f"  Countries table not found")
                return None

            print(f"  Found countries table")
            countries = {}

            # Extract country data
            rows = countries_table.find_all('tr', {'data-testid': 'etf-holdings_countries_row'})

            for row in rows:
                country_td = row.find('td', {'data-testid': 'tl_etf-holdings_countries_value_name'})
                percentage_span = row.find('span', {'data-testid': 'tl_etf-holdings_countries_value_percentage'})

                if country_td and percentage_span:
                    country_text = country_td.get_text(strip=True)
                    percentage_text = percentage_span.get_text(strip=True)

                    try:
                        percentage = float(percentage_text.replace('%', '').strip())

                        # Validate percentage and country name
                        if 0 < percentage <= 100 and country_text in self.VALID_COUNTRIES:
                            countries[country_text] = percentage
                    except ValueError:
                        continue

            if countries:
                print(f"  ✓ Found {len(countries)} countries: {list(countries.keys())}")
                return countries
            else:
                print(f"  ✗ No country data found")
                return None

        except Exception as e:
            print(f"  ✗ Error: {e}")
            return None
