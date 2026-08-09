# Portfolio Analytics Platform

A Flask web application for tracking a stock portfolio, recording trades, and exploring market data. It provides portfolio insights, allocation breakdowns, position-sizing calculations, quote history, and transaction records in a responsive interface.

## Features

- Account registration and login with password hashing and session-based access control
- Portfolio dashboard with current value, largest winner and loser, and best and worst performing positions
- Stock and sector allocation breakdowns with interactive charts
- Buy, sell, and cash-deposit workflows with validation against available cash and holdings
- Position-sizing calculator based on risk per trade, entry price, and stop loss
- Stock quote lookup with historical area and candlestick charts
- Transaction history for all completed trades
- SQLite-backed market-data caching to limit repeat API requests

## Built with

- Python and Flask
- SQLite
- Bootstrap 5
- Chart.js and Lightweight Charts
- Finnhub API for quotes and company metadata
- Twelve Data API for historical price data

## Prerequisites

- Python 3.10 or later
- A Finnhub API key
- A Twelve Data API key

## Installation

1. Clone the repository and open its directory.

2. Create and activate a virtual environment.

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Install the dependencies.

   ```powershell
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root.

   ```env
   SECRET_KEY=replace-with-a-long-random-secret
   DB_PATH=platform.db
   FINNHUB_API_KEY=your-finnhub-api-key
   TWELVE_DATA_API_KEY=your-twelve-data-api-key
   ```

   The application reads these variables through `python-dotenv`. Keep `.env` private; it is excluded from version control.

5. Ensure the SQLite database contains the required tables, then start the development server.

   ```powershell
   flask --app app run --debug
   ```

6. Open the local URL shown in the terminal, usually `http://127.0.0.1:5000`, then register an account.

## Project structure

```text
app.py          Flask routes, authentication, and portfolio workflows
api.py          Market-data requests and cache handling
database.py     SQLite connection helper
helpers.py      Portfolio calculations, formatting, and route helpers
templates/      HTML page templates
static/         CSS, JavaScript, and image assets
platform.db     Local SQLite database (not committed)
```

## Notes

- Market prices and historical data depend on the availability and limits of the configured third-party API accounts.
- This project is intended for personal portfolio tracking and educational use. It does not provide financial advice.
