import finnhub

API_KEY = "d930frhr01qpou38ohv0d930frhr01qpou38ohvg"

finnhub_client = finnhub.Client(api_key=API_KEY)

def get_quote(symbol:str):
    symbol = symbol.upper()

    data = finnhub_client.quote(symbol)

    return {
        "symbol": symbol, 
        "current_price": data["c"], 
        "change": data["d"],
        "percent_change": data["dp"],
        "high": data["h"],
        "low": data["l"],
        "open": data["o"],
        "previous_close": data["pc"]
    }