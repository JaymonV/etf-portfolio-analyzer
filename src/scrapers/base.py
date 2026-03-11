"""Base scraper class for JustETF data extraction.

This module provides the abstract base class for web scrapers that extract
ETF allocation data from JustETF.com using Selenium WebDriver.
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, Optional

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# Configure module logger
logger = logging.getLogger(__name__)


class ScraperError(Exception):
    """Base exception for scraper-related errors."""

    pass


class DriverSetupError(ScraperError):
    """Exception raised when WebDriver setup fails."""

    pass


class PageLoadError(ScraperError):
    """Exception raised when page loading fails."""

    pass


class JustETFScraper(ABC):
    """Abstract base class for JustETF web scrapers.

    This class provides common functionality for scraping ETF allocation data
    from JustETF.com, including WebDriver setup, page loading, and element
    interaction. Subclasses implement the specific scraping logic.

    Attributes:
        driver: Selenium WebDriver instance for browser automation.
        headless: Whether to run browser in headless mode.

    Example:
        class MyScraper(JustETFScraper):
            def scrape(self, isin: str) -> Optional[Dict[str, float]]:
                # Implementation
                pass

        with MyScraper() as scraper:
            data = scraper.scrape('IE00B4L5Y983')
    """

    # Default wait times (in seconds)
    DEFAULT_PAGE_LOAD_WAIT = 3.0
    DEFAULT_BUTTON_CLICK_WAIT = 2.0

    def __init__(self, headless: bool = True) -> None:
        """Initialize scraper with Selenium WebDriver.

        Args:
            headless: Whether to run browser in headless mode. Defaults to True.
        """
        self.driver: Optional[webdriver.Chrome] = None
        self.headless = headless
        logger.debug(f"Initialized {self.__class__.__name__} (headless={headless})")

    def _setup_driver(self) -> webdriver.Chrome:
        """Set up and configure Selenium WebDriver.

        Returns:
            Configured Chrome WebDriver instance.

        Raises:
            DriverSetupError: If WebDriver initialization fails.
        """
        logger.info("Setting up Chrome WebDriver")

        try:
            chrome_options = Options()

            # Headless mode
            if self.headless:
                chrome_options.add_argument("--headless")
                logger.debug("Running in headless mode")

            # Performance and stability options
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-extensions")

            # Set user agent to avoid bot detection
            chrome_options.add_argument(
                "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )

            # Suppress logging
            chrome_options.add_argument("--log-level=3")
            chrome_options.add_experimental_option(
                "excludeSwitches", ["enable-logging"]
            )

            driver = webdriver.Chrome(options=chrome_options)
            logger.info("WebDriver initialized successfully")
            return driver

        except WebDriverException as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            raise DriverSetupError(
                f"Failed to initialize Chrome WebDriver: {str(e)}. "
                "Ensure Chrome and ChromeDriver are installed."
            ) from e

    def _get_page(
        self, url: str, wait_time: float = DEFAULT_PAGE_LOAD_WAIT
    ) -> BeautifulSoup:
        """Load page and return BeautifulSoup object.

        Args:
            url: URL to fetch.
            wait_time: Time to wait for page load in seconds. Defaults to 3.0.

        Returns:
            BeautifulSoup object of page source.

        Raises:
            PageLoadError: If page loading fails.
        """
        if not self.driver:
            raise ScraperError("WebDriver not initialized. Use context manager.")

        logger.debug(f"Loading page: {url}")

        try:
            self.driver.get(url)
            time.sleep(wait_time)

            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            logger.debug("Page loaded successfully")
            return soup

        except WebDriverException as e:
            logger.error(f"Failed to load page {url}: {e}")
            raise PageLoadError(
                f"Failed to load page {url}: {str(e)}"
            ) from e

    def _click_show_more(self, data_testid: str) -> bool:
        """Click 'show more' button if it exists.

        Args:
            data_testid: The data-testid attribute of the button.

        Returns:
            True if button was found and clicked, False otherwise.
        """
        if not self.driver:
            raise ScraperError("WebDriver not initialized. Use context manager.")

        try:
            button = self.driver.find_element(
                By.CSS_SELECTOR, f'[data-testid="{data_testid}"]'
            )
            logger.debug(f"Found 'show more' button: {data_testid}")

            # Scroll to button and click using JavaScript
            self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
            time.sleep(1)
            self.driver.execute_script("arguments[0].click();", button)

            logger.info(f"Clicked 'show more' button: {data_testid}")
            time.sleep(self.DEFAULT_BUTTON_CLICK_WAIT)
            return True

        except NoSuchElementException:
            logger.debug(f"No 'show more' button found: {data_testid}")
            return False
        except WebDriverException as e:
            logger.warning(f"Failed to click 'show more' button: {e}")
            return False

    @abstractmethod
    def scrape(self, isin: str) -> Optional[Dict[str, float]]:
        """Scrape data for given ISIN.

        This method must be implemented by subclasses to define specific
        scraping logic for different data types (countries, sectors, etc.).

        Args:
            isin: ISIN code of the ETF.

        Returns:
            Dictionary mapping categories to percentage allocations,
            or None if no data found.

        Raises:
            ScraperError: If scraping fails.
        """
        pass

    def close(self) -> None:
        """Close the WebDriver and cleanup resources."""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("WebDriver closed successfully")
            except Exception as e:
                logger.warning(f"Error closing WebDriver: {e}")
            finally:
                self.driver = None

    def __enter__(self):
        """Context manager entry - initialize WebDriver."""
        logger.debug(f"Entering context manager for {self.__class__.__name__}")
        self.driver = self._setup_driver()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup WebDriver."""
        logger.debug(f"Exiting context manager for {self.__class__.__name__}")
        self.close()
        return False  # Don't suppress exceptions
