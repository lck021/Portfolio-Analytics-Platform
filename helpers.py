from functools import wraps
import sqlite3
from datetime import date, datetime

from flask import redirect, render_template, render_template_string, request, session
from api import *


def login_required(func) -> None:
    """Directs user to login if they have not, else process the request"""

    @wraps(func)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return func(*args, **kwargs)
    
    return decorated_function


def error(code, title, message):
    """Returns custom error message"""

    return render_template('error.html', code=code, title=title, message=message)


def db_connect():
    """Connects to sqlite database"""

    connection = sqlite3.connect("platform.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    return cursor, connection


def sgd(value):
    """Format value as SGD."""

    return f"${value:,.2f}"


def calculate_portfolio_value(user_id):
    """Returns a dictionary containing the user's portfolio, total portfolio value, holdings value, and cash value"""

    cursor, connection = db_connect()

    try:
        data = cursor.execute("select symbol, sum(shares) as total_shares from transactions where user_id=? group by symbol", (user_id,)).fetchall()
        portfolio = [dict(stock) for stock in data]

        current_cash = cursor.execute("select cash from users where id=?", (user_id,)).fetchone()["cash"]
        total = current_cash

        for stock in portfolio: # adds cash from each stock into total, 'stock' is a dictionary
            current_price = get_quote(stock['symbol'])["current_price"]
            stock['price'] = current_price
            stock['total'] = round(stock['total_shares'] * current_price, 2)
            total += stock['total']

        holdings_value = total - current_cash
        
        return {
            "portfolio": portfolio,
            "total_value": total, 
            "holdings_value": holdings_value,
            "cash_value": current_cash
        }

    finally:
        connection.close()


def cache_daily_portfolio():
    """Caches the daily portfolio value of all users"""

    cursor, connection = db_connect()
    today = date.today().isoformat()

    try:
        users = cursor.execute("select id from users").fetchall()

        for user in users:
            portfolio_info = calculate_portfolio_value(user["id"])

            cursor.execute("insert into portfolio_value_history (user_id, snapshot_date, total_value, cash_value, holdings_value)" \
            "values (?, ?, ?, ?, ?)" \
            "on conflict (user_id, snapshot_date)" \
            "do update set " \
            "total_value = excluded.total_value, " \
            "cash_value = excluded.cash_value, " \
            "holdings_value = excluded.holdings_value, " \
            "created_at = current_timestamp", 
            (user["id"], today, portfolio_info["total_value"], portfolio_info["cash_value"], portfolio_info["holdings_value"]))

            connection.commit()

    finally:
        connection.close()