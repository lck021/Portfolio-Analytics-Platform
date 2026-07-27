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


def is_valid_quote(data):
    """Checks if returned quote from finnhub is valid"""

    return (
        data.get("c") not in (None, 0) and 
        data.get("pc") not in (None, 0) and 
        data.get("t") not in (None, 0)
    )


def get_quote(symbol:str):
    """Gets quote for a certain stock symbol"""

    symbol = symbol.upper()

    data = finnhub_client.quote(symbol)

    if not is_valid_quote(data):
        return None

    return {
        "symbol": symbol, 
        "current_price": data['c'], 
        "change": data['d'],
        "percent_change": data['dp'],
        "high": data['h'],
        "low": data['l'],
        "open": data['o'],
        "previous_close": data['pc']
    }


def get_metadata(symbol:str):
    """Gets metadata of a certain stock symbol"""

    cursor, connection = db_connect()
    today = datetime.today().date()
    symbol = symbol.strip().upper()

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
    """Gets stock historical performance of a certain resolution and range"""

    cursor, connection = db_connect()
    symbol = symbol.strip().upper()

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
        if range not in RANGES:
            return Exception("Wrong input range")
        
        settings = RANGES[range]
        interval = settings["interval"]
        days = settings["days"]
        output_size = OUTPUT_SIZES[interval]
        today_dt = datetime.now(timezone.utc)

        start_date = (today_dt - timedelta(days=days)).isoformat()
        end_date = today_dt.isoformat()

        # check cache
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

            return [{"time": row["datetime"], "value": row["close"]} for row in rows]

        #if there is a cache and cache is up to date
        elif not is_cache_stale(interval=interval, last_cached_dt=last_cached_value):
            cached_data = cursor.execute(
                                        """
                                        SELECT *
                                        FROM historical_prices
                                        WHERE symbol = ?
                                        AND interval = ?
                                        AND datetime >= ?
                                        ORDER BY datetime
                                        """,
                                        (symbol, interval, start_date)).fetchall()
            return [{"time": row["datetime"], "value": row["close"]} for row in cached_data]

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
                                    symbol, interval, candle["datetime"],
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

        return [{"time": row["datetime"], "value": row["close"]} for row in rows]

    finally:
        connection.close()


def is_cache_stale(interval, last_cached_dt: datetime.isoformat):
    """Checks if the stored historical performance in the db is stale given a certain time interval"""

    now = datetime.now(timezone.utc)
    last_cached_dt = datetime.fromisoformat(last_cached_dt).replace(tzinfo=timezone.utc)
    age = now - last_cached_dt

    if interval == "1day":
        #checks if a full day has elapsed since the last cached date and if the market has closed
        return last_cached_dt.date() < now.date() and now.hour >= MARKET_CLOSE_UTC
    elif interval == "1week":
        return age > timedelta(days=6)
    elif interval == "1h":
        return age > timedelta(hours=1)
    elif interval == "15min":
        return age > timedelta(minutes=15)
    return True

print(get_stock_history(symbol="AAPL", range="1W"))