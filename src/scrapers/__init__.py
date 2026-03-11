"""Web scrapers for ETF data from JustETF."""

from .country_scraper import CountryScraper
from .sector_scraper import SectorScraper

__all__ = ['CountryScraper', 'SectorScraper']
