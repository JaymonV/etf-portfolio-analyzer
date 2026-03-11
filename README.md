# Portfolio Rebalancer

When building a portfolio of ETFs, it's easy to end up with unintended concentration. For example, the S&P 500 currently has ~35% of its weight in just 10 companies, and multiple ETFs in your portfolio may all hold the same underlying stocks. This tool helps you see through that — by scraping sector and geographic allocation data from [JustETF.com](https://www.justetf.com/) for each ETF and aggregating it across your whole portfolio.

By setting fixed target allocations per sector and region, you take emotion out of the equation: instead of chasing what's hot or panic-avoiding what's down, you simply buy whichever category is most underweight. This naturally means buying low and not piling into what's already high.

Designed for **Degiro** CSV exports, but works with any CSV containing ISIN codes.

## Requirements

- Python 3.10+
- Chrome/Chromium (ChromeDriver is managed automatically by Selenium 4.6+)

## Installation

```bash
git clone https://github.com/jaymonv/etf-portfolio-analyzer.git
cd etf-portfolio-analyzer
# Change to python3X if you have any Python < 3.10 installed
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
```

## Usage

### 1. Export your Degiro portfolio

In Degiro: Portfolio → Export → CSV. Save as `data/Portfolio.csv`.

### 2. Run analysis

```bash
# Geographic/country breakdown
python scripts/analyze_countries.py

# Sector breakdown
python scripts/analyze_sectors.py
```

Results are printed to the console and saved as CSV files in `data/`.

### Sample output

**Geographic distribution by country** (`data/output/countries.csv`):

| Country       | Percentage |
|---------------|------------|
| United States | 62.45      |
| Japan         | 6.12       |
| United Kingdom| 4.38       |
| France        | 3.21       |
| Germany       | 2.89       |
| Canada        | 2.74       |
| Switzerland   | 2.11       |
| India         | 1.98       |
| ...           | ...        |

**Geographic distribution by region** (`data/output/regions.csv`):

| Region                         | Percentage |
|--------------------------------|------------|
| United States                  | 62.45      |
| Europe                         | 16.84      |
| Japan                          | 6.12       |
| Emerging Markets               | 8.33       |
| Developed Asia-Pacific (ex-Japan) | 4.17    |
| Canada                         | 2.74       |
| Other                          | 0.35       |

**Sector distribution** (`data/output/sectors.csv`):

| Sector                 | Percentage |
|------------------------|------------|
| Technology             | 28.34      |
| Financials             | 14.52      |
| Health Care            | 11.23      |
| Industrials            | 9.87       |
| Consumer Discretionary | 9.41       |
| Consumer Staples       | 6.72       |
| Energy                 | 4.38       |
| Materials              | 3.91       |
| Utilities              | 3.12       |
| Real Estate            | 2.84       |
| Communication Services | 5.66       |

### Target allocations

Edit `data/input/targets.json` to define your desired portfolio weights. These serve as a reference when interpreting the output — compare the actual distribution against your targets to decide which ETF to buy next.

```json
{
  "regions": {
    "United States": 50,
    "Europe": 26,
    "Japan": 8,
    "Developed Asia-Pacific (ex-Japan)": 6,
    "Canada": 3,
    "Emerging Markets": 7
  },
  "sectors": {
    "Technology": 17,
    "Financials": 15,
    "Industrials": 13,
    "Health Care": 10,
    "Consumer Staples": 9,
    "Consumer Discretionary": 8,
    "Telecommunication": 8,
    "Energy": 7,
    "Real Estate": 5,
    "Materials": 4,
    "Utilities": 4
  }
}
```

All values are percentages and should sum to 100 per category. When `targets.json` is present, each script prints an additional comparison table sorted by delta — most underweight first, so the top row tells you what to buy next:

| Region           | Actual | Target | Delta |
|------------------|--------|--------|-------|
| Emerging Markets | 5.10   | 7      | -1.90 |
| Canada           | 1.84   | 3      | -1.16 |
| Japan            | 7.20   | 8      | -0.80 |
| Europe           | 16.84  | 16     | +0.84 |
| United States    | 63.29  | 50     | +13.29|

### Rate limiting

If JustETF blocks requests, increase the delay between scrapes:

```python
# In scripts/analyze_countries.py or scripts/analyze_sectors.py
analyzer = CountryAnalyzer(portfolio, rate_limit=15.0)  # seconds between requests
```

## CSV Format (Degiro)

Columns are matched by **position**, so any language export works (Dutch, English, German, French, etc.):

| Position | Dutch | English |
|----------|-------|---------|
| 0 | Product | Product |
| 1 | Symbool/ISIN | Symbol/ISIN |
| 2 | Aantal | Amount |
| 3 | Waarde in EUR | Value in EUR |

```csv
Product,Symbool/ISIN,Aantal,Waarde in EUR
VANGUARD FTSE ALL-WORLD,IE00BK5BQT80,51,"7253.22"
ISHARES MSCI WORLD SRI,IE00BYX2JD69,260,"3072.16"
```

For other brokers, update the column index constants in [src/portfolio.py](src/portfolio.py).

## Project Structure

```
├── scripts/
│   ├── analyze_countries.py   # CLI: geographic analysis
│   └── analyze_sectors.py     # CLI: sector analysis
├── src/
│   ├── portfolio.py           # Portfolio CSV loading
│   ├── analyzers/
│   │   ├── country_analyzer.py
│   │   └── sector_analyzer.py
│   └── scrapers/
│       ├── base.py            # Selenium base scraper
│       ├── country_scraper.py
│       └── sector_scraper.py
├── tests/
└── data/                      # Your portfolio data (gitignored)
```

## License

GNU GPL v3
