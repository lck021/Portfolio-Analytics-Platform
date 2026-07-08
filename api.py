import finnhub

API_KEY = "d930frhr01qpou38ohv0d930frhr01qpou38ohvg"

finnhub_client = finnhub.Client(api_key=API_KEY)

def is_valid_quote(data):
    return (
        data.get("c") not in (None, 0) and 
        data.get("pc") not in (None, 0) and 
        data.get("t") not in (None, 0)
    )


def get_quote(symbol:str):
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