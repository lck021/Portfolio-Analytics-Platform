import os
from dotenv import load_dotenv

load_dotenv()

import finnhub
from twelvedata import TDClient
from datetime import timezone, datetime, timedelta

from database import db_connect

FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY")
TWELVE_DATA_API_KEY = os.environ.get("TWELVE_DATA_API_KEY")

finnhub_client = finnhub.Client(api_key=FINNHUB_API_KEY)
td_client = TDClient(apikey=TWELVE_DATA_API_KEY)

MARKET_CLOSE_UTC = 20  # ~4pm ET in UTC


def is_valid_ticker(symbol):
    """Checks if a ticker is valid, using cache to avoid redundant API calls"""

    symbol = symbol.strip().upper()
    cursor, connection = db_connect()

    try:
        # check cache first
        row = cursor.execute("SELECT * FROM ticker_validity_cache WHERE symbol = ?", (symbol,)).fetchone()
        last_checked = row["checked_at"] if row is not None else None

        # if there is no cache or if it is stale
        if last_checked is None or not ticker_cache_valid(last_checked):

            data = finnhub_client.quote(symbol)

            valid = (
                data.get("c") not in (None, 0) and
                data.get("pc") not in (None, 0) and
                data.get("t") not in (None, 0)
            )

            cursor.execute("""
                INSERT INTO ticker_validity_cache (
                    symbol,
                    is_valid,
                    checked_at
                )
                VALUES (?, ?, ?)
                ON CONFLICT(symbol) DO UPDATE SET
                    is_valid = excluded.is_valid,
                    checked_at = excluded.checked_at
            """, (
                symbol,
                int(valid),
                datetime.now().isoformat()
            ))
            connection.commit()

            row = cursor.execute(
                "SELECT * FROM ticker_validity_cache WHERE symbol = ?", (symbol,)
            ).fetchone()

        return bool(row["is_valid"])

    finally:
        connection.close()


def ticker_cache_valid(last_updated):
    """
    Returns True if cached ticker is still valid.
    """
    last_updated = datetime.fromisoformat(last_updated).replace(tzinfo=timezone.utc)
    age = datetime.now(timezone.utc) - last_updated

    return age < timedelta(hours=24)


def get_quote(symbol):
    """Gets quote for a certain stock symbol, using cache to avoid redundant API calls"""

    symbol = symbol.strip().upper()
    cursor, connection = db_connect()

    if not is_valid_ticker(symbol):
        return None

    try: 
        #check cache first
        row = cursor.execute("SELECT * FROM quote_cache WHERE symbol = ?", (symbol,)).fetchone()
        last_cached_value = row["updated_at"] if row is not None else None

        #if there is no cache or if it is not valid
        if last_cached_value is None or not quote_cache_valid(last_cached_value):

            #gets data from api
            data = finnhub_client.quote(symbol)

            quote = {
                        "symbol": symbol,
                        "current_price": data["c"],
                        "change": data["d"],
                        "percent_change": data["dp"],
                        "high": data["h"],
                        "low": data["l"],
                        "open": data["o"],
                        "previous_close": data["pc"]
                    }

            #upsert cache
            cursor.execute("""
                                INSERT INTO quote_cache (
                                    symbol,
                                    current_price,
                                    change,
                                    percent_change,
                                    high,
                                    low,
                                    open,
                                    previous_close,
                                    updated_at
                                )
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                                ON CONFLICT(symbol) DO UPDATE SET
                                    current_price = excluded.current_price,
                                    change = excluded.change,
                                    percent_change = excluded.percent_change,
                                    high = excluded.high,
                                    low = excluded.low,
                                    open = excluded.open,
                                    previous_close = excluded.previous_close,
                                    updated_at = excluded.updated_at
                            """, (
                                symbol,
                                quote["current_price"],
                                quote["change"],
                                quote["percent_change"],
                                quote["high"],
                                quote["low"],
                                quote["open"],
                                quote["previous_close"],
                                datetime.now().isoformat()
                            ))
            connection.commit()

            row = cursor.execute("SELECT * FROM quote_cache WHERE symbol = ?", (symbol,)).fetchone()

        #returns required info
        return {
            "symbol": row["symbol"],
            "current_price": row["current_price"],
            "change": row["change"],
            "percent_change": row["percent_change"],
            "high": row["high"],
            "low": row["low"],
            "open": row["open"],
            "previous_close": row["previous_close"]
        }
    
    finally:
        connection.close()


def quote_cache_valid(last_updated):
    """Returns True if cached quote is still valid"""

    last_updated = datetime.fromisoformat(last_updated).replace(tzinfo=timezone.utc)
    age = datetime.now(timezone.utc) - last_updated

    return age < timedelta(seconds=30)


def get_metadata(symbol:str):
    """Gets metadata of a certain stock symbol, using cache to avoid redundant API calls"""

    cursor, connection = db_connect()
    today = datetime.today().date()
    symbol = symbol.strip().upper()

    if not is_valid_ticker(symbol):
        return None

    try:
        metadata = cursor.execute("select * from stock_metadata where ticker=?", (symbol,)).fetchone()

        if metadata is None: # if metadata has not been cached yet
            metadata = finnhub_client.company_profile2(symbol=symbol)
            print(metadata)
            cursor.execute(
                            """
                            INSERT INTO stock_metadata (
                                ticker,
                                name,
                                industry,
                                exchange,
                                country,
                                currency,
                                last_updated
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                symbol,
                                metadata["name"],
                                metadata["finnhubIndustry"],
                                metadata["exchange"],
                                metadata["country"],
                                metadata["currency"],
                                today
                            )
                        )
            connection.commit()

        # else if stock metadata is already cached
        else:
            last_updated = datetime.strptime(metadata["last_updated"], "%Y-%m-%d").date()

            # if cached data is already stale
            if today - last_updated > timedelta(days=30):
                metadata = finnhub_client.company_profile2(symbol=symbol)

                cursor.execute(
                                """
                                UPDATE stock_metadata
                                SET
                                    name = ?,
                                    industry = ?,
                                    exchange = ?,
                                    country = ?,
                                    currency = ?,
                                    last_updated = ?
                                    WHERE ticker = ?
                                """, (
                                    metadata["name"],
                                    metadata["finnhubIndustry"],
                                    metadata["exchange"],
                                    metadata["country"],
                                    metadata["currency"],
                                    today,
                                    symbol
                                ))
                connection.commit()
        
        metadata = cursor.execute("select * from stock_metadata where ticker=?", (symbol,)).fetchone()

        return {
                "symbol": metadata["ticker"],
                "name": metadata["name"],
                "industry": metadata["industry"],
                "exchange": metadata["exchange"],
                "country": metadata["country"],
                "currency": metadata["currency"],
            }

    finally: 
        connection.close()


def get_stock_history(symbol, range):
    """Gets stock historical performance of a certain resolution and range, using cache to avoid redundant API calls"""

    cursor, connection = db_connect()
    symbol = symbol.strip().upper()

    if not is_valid_ticker(symbol):
        return None

    RANGES = {
                "1W": {
                    "interval": "15min",
                    "days": 7
                },
                "1M": {
                    "interval": "1h",
                    "days": 30
                },
                "6M": {
                    "interval": "1day",
                    "days": 180
                },
                "1Y": {
                    "interval": "1day",
                    "days": 365
                },
                "5Y": {
                    "interval": "1week",
                    "days": 365 * 5
                }
            }

    OUTPUT_SIZES = {
                "15min": 700,
                "1h": 750,
                "1day": 365,
                "1week": 260
            }

    try:        
        settings = RANGES[range]
        interval = settings["interval"]
        days = settings["days"]
        output_size = OUTPUT_SIZES[interval]
        today_dt = datetime.now(timezone.utc)

        start_date = (today_dt - timedelta(days=days)).isoformat()
        end_date = today_dt.isoformat()

        #check cache
        row = cursor.execute("SELECT MAX(datetime) FROM historical_prices WHERE symbol = ? AND interval = ?", (symbol, interval)).fetchone()
        last_cached_value = row[0] if row is not None else None

        #if there is no cache
        if last_cached_value is None:

            #gets data from api
            ts = td_client.time_series(
                symbol=symbol, 
                interval=interval, 
                timezone="UTC", 
                start_date=start_date, 
                end_date=end_date, 
                outputsize=output_size
            )

            candles = ts.as_json()

            #adds data into database
            for candle in candles:
                cursor.execute(
                                """
                                INSERT INTO historical_prices (
                                    symbol,
                                    interval,
                                    datetime,
                                    open,
                                    high,
                                    low,
                                    close,
                                    volume
                                )
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)

                                ON CONFLICT(symbol, interval, datetime)
                                DO UPDATE SET
                                    open = excluded.open,
                                    high = excluded.high,
                                    low = excluded.low,
                                    close = excluded.close,
                                    volume = excluded.volume;
                                """,
                                (
                                    symbol,
                                    interval,
                                    datetime.fromisoformat(candle["datetime"]).isoformat(),
                                    float(candle["open"]),
                                    float(candle["high"]),
                                    float(candle["low"]),
                                    float(candle["close"]),
                                    int(candle["volume"])
                                )
                            )
            connection.commit()

            #reads database again
            rows = cursor.execute(
                                    """
                                    SELECT *
                                    FROM historical_prices
                                    WHERE symbol = ?
                                    AND interval = ?
                                    AND datetime >= ?
                                    ORDER BY datetime
                                    """,
                                    (
                                        symbol,
                                        interval,
                                        start_date
                                    )
                                ).fetchall()

            return [{"time": iso_to_unix(row["datetime"]), 
                     "open": row["open"],
                     "high": row["high"],
                     "low": row["low"],
                     "close": row["close"]} for row in rows]

        #if there is a cache and cache is up to date
        elif historical_cache_valid(interval=interval, last_cached_dt=last_cached_value):
            rows = cursor.execute(
                                        """
                                        SELECT *
                                        FROM historical_prices
                                        WHERE symbol = ?
                                        AND interval = ?
                                        AND datetime >= ?
                                        ORDER BY datetime
                                        """,
                                        (symbol, interval, start_date)).fetchall()
            
            return [{"time": iso_to_unix(row["datetime"]), 
                                 "open": row["open"],
                                 "high": row["high"],
                                 "low": row["low"],
                                 "close": row["close"]} for row in rows]

        #if there is a cache and it is not up to date
        else:
            
            #gets data from api
            ts = td_client.time_series(
                symbol=symbol, 
                interval=interval, 
                timezone="UTC", 
                start_date=last_cached_value,
                outputsize=output_size
            )
            candles = ts.as_json()

            for candle in candles:
                cursor.execute(
                                """
                                INSERT INTO historical_prices (
                                    symbol, interval, datetime, open, high, low, close, volume
                                )
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                ON CONFLICT(symbol, interval, datetime)
                                DO UPDATE SET
                                    open = excluded.open,
                                    high = excluded.high,
                                    low = excluded.low,
                                    close = excluded.close,
                                    volume = excluded.volume;
                                """,
                                (
                                    symbol, 
                                    interval, 
                                    datetime.fromisoformat(candle["datetime"]).isoformat(),
                                    float(candle["open"]), float(candle["high"]),
                                    float(candle["low"]), float(candle["close"]),
                                    int(candle["volume"])
                                )
                            )
            connection.commit()

            rows = cursor.execute(
                                    """
                                    SELECT * FROM historical_prices
                                    WHERE symbol = ? AND interval = ? AND datetime >= ?
                                    ORDER BY datetime
                                    """,
                                    (symbol, interval, start_date)
                                ).fetchall()

        return [{"time": iso_to_unix(row["datetime"]), 
                             "open": row["open"],
                             "high": row["high"],
                             "low": row["low"],
                             "close": row["close"]} for row in rows]

    finally:
        connection.close()


def historical_cache_valid(interval, last_cached_dt: datetime.isoformat):
    """Checks if the stored historical performance in the db is stale given a certain time interval"""

    now = datetime.now(timezone.utc)
    last_cached_dt = datetime.fromisoformat(last_cached_dt).replace(tzinfo=timezone.utc)
    age = now - last_cached_dt

    if interval == "1day":
        #checks if a full day has elapsed since the last cached date and if the market has closed
        return last_cached_dt.date() == now.date() and now.hour < MARKET_CLOSE_UTC
    elif interval == "1week":
        return age < timedelta(days=6)
    elif interval == "1h":
        return age < timedelta(hours=1)
    elif interval == "15min":
        return age < timedelta(minutes=15)
    return False

def iso_to_unix(dt_iso):
    """Converts an iso string into a unix timestamp to be used for LightWeight Charts"""
    dt = datetime.fromisoformat(dt_iso)

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return int(dt.timestamp())