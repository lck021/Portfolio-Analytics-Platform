import os
import finnhub
from datetime import date, datetime, timedelta

from database import db_connect

API_KEY = os.environ.get("API_KEY")

finnhub_client = finnhub.Client(api_key=API_KEY)

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

    try:
        metadata = cursor.execute("select * from stock_metadata where ticker=?", (symbol,)).fetchone()

        if metadata is None: # if metadata has not been cached yet
            metadata = finnhub_client.company_profile2(symbol=symbol)
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
                                metadata["ticker"],
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
