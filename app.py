import os
from types import MethodDescriptorType
from dotenv import load_dotenv

load_dotenv()

import sqlite3
import math
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import *
from api import *
from database import db_connect

# Configure application
app = Flask(__name__)

# Configure cookies
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")

# Custom filter
app.jinja_env.filters["sgd"] = sgd

# Prevents app from caching and returning old information
@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show homepage dashboard"""
    
    return render_template('dashboard.html')


@app.route("/api/dashboard", methods=["GET"])
@login_required
def calculate_dashboard():
    """Calculates needed info to display biggest winner, loser, and best and worst performing position"""

    user_id = session['user_id']
    portfolio_info = calculate_portfolio_value(user_id)

    dollar_change = {}
    percent_change = {}

    for stock in portfolio_info["portfolio"]:
        market_value = stock["total"]
        cost_basis = stock["total_shares"] * calculate_average_cost(stock["symbol"])

        profit_loss = market_value - cost_basis

        percent_return = (profit_loss / cost_basis) 

        percent_of_portfolio = market_value / portfolio_info["total_value"] 

        dollar_change[stock["symbol"]] = {"cost_basis": cost_basis,"profit_loss": profit_loss, "percent_return": percent_return}
        percent_change[stock["symbol"]] = {"percent_return": percent_return, "percent_of_portfolio": percent_of_portfolio}

    aescend_dollar_change = list(sorted(dollar_change.items(), key=lambda item: item[1]["profit_loss"]))
    aescend_percent_change = list(sorted(percent_change.items(), key=lambda item: item[1]["percent_return"]))

    return jsonify({
        "portfolio_value": portfolio_info["total_value"],
        "largest_winner": {
            "symbol": aescend_dollar_change[-1][0],
            "cost_basis": aescend_dollar_change[-1][1]["cost_basis"],
            "profit_loss": aescend_dollar_change[-1][1]["profit_loss"],
            "percent_return": aescend_dollar_change[-1][1]["percent_return"]
        },
        "largest_loser": {
            "symbol": aescend_dollar_change[0][0],
            "cost_basis": aescend_dollar_change[0][1]["cost_basis"],
            "profit_loss": aescend_dollar_change[0][1]["profit_loss"],
            "percent_return": aescend_dollar_change[0][1]["percent_return"]
        },
        "best_position": {
            "symbol": aescend_percent_change[-1][0],
            "percent_return": aescend_percent_change[-1][1]["percent_return"],
            "percent_of_portfolio": aescend_percent_change[-1][1]["percent_of_portfolio"]
        },
        "worst_position": {
            "symbol": aescend_percent_change[0][0],
            "percent_return": aescend_percent_change[0][1]["percent_return"],
            "percent_of_portfolio": aescend_percent_change[0][1]["percent_of_portfolio"]
        }
    })

@app.route('/breakdown')
@login_required
def breakdown():
    """Displays portfolio breakdown"""

    user_id = session['user_id']
    cursor, connection = db_connect()
    current_cash = cursor.execute("select cash from users where id=?", (session["user_id"],)).fetchone()["cash"]

    try:
        # returns a list containing dictionaries with symbol and total_share fields
        portfolio_info = calculate_portfolio_value(user_id)
        portfolio = portfolio_info["portfolio"]
        total = portfolio_info["total_value"]

        stock_data = []
        stock_data_master = []
        other_stock_label = []
        other_stock_value = 0

        sector_data = {}
        sector_data_master = {}
        other_sector_label = []
        other_sector_value = 0

        for stock in portfolio: 
            # adds all stock data into a master list first
            stock_data_master.append({"symbol": stock['symbol'].strip().upper(), "total": stock['total']})

            # combines smaller stocks into an 'others' category
            percentage = stock['total'] / total * 100

            if percentage < 5.0:
                other_stock_label.append(stock['symbol'])
                other_stock_value += stock['total']
            
            else:
                stock_data.append({"symbol": stock['symbol'].strip().upper(), "total": stock['total']})

            # creates sectoral data and adds it into a master list first
            sector = get_metadata(stock['symbol'])["industry"]
            sector_data_master[sector] = sector_data.get(sector, 0) + stock['total']

        # adds cash and others field if present to stock_data
        if other_stock_value > 0 and len(other_sector_label) > 1:
            stock_data.append({"symbol" : "Cash", "total": current_cash})
            stock_data.append({"symbol": f"Others - {' '.join(other_stock_label)}", "total": other_stock_value})
        else:
            stock_data_master.append({"symbol" : "Cash", "total": current_cash})
            stock_data = stock_data_master


        # combines smaller sectors into an 'others' category
        for sector, sector_value in sector_data_master.items():
            percentage = sector_value / total * 100

            if percentage < 5.0:
                other_sector_label.append(sector)
                other_sector_value += sector_value

            else:
                sector_data[sector] = sector_data.get(sector, 0) + sector_value

        # adds cash and others field if present to sector data
        if other_sector_value > 0 and len(other_sector_label) > 1:
            sector_data["Cash"] = current_cash
            sector_data[f"Others - {' '.join(other_sector_label)}"] = other_sector_value
        else:
            sector_data_master["Cash"] = current_cash
            sector_data = sector_data_master

        return render_template('breakdown.html', portfolio=portfolio, current_cash=current_cash, total=total, stock_data=stock_data, sector_data=sector_data)
    
    finally:
        connection.close()


@app.route("/sizing", methods=["GET", "POST"])
@login_required
def sizing():
    """Calculate position sizing"""

    cursor, connection = db_connect()
    user_id = session["user_id"]
    portfolio_info = calculate_portfolio_value(user_id)
    total = portfolio_info["total_value"]
    cash = portfolio_info["cash_value"]

    try:
        if request.method == "POST": # if user submitted for calculation
            # getting raw data for calculation

            risk_per_trade = request.form.get("risk_per_trade")
            entry_price = request.form.get("entry_price")
            stop_loss = request.form.get("stop_loss")

            if not risk_per_trade.replace(".", "", 1).isdigit() or not entry_price.replace(".", "", 1).isdigit() or not stop_loss.replace(".", "", 1).isdigit():
                return error(400, "Bad Request", "Please provide valid inputs.")

            risk_per_trade = float(risk_per_trade)
            entry_price = float(entry_price)
            stop_loss = float(stop_loss)

            if risk_per_trade <= 0 or entry_price <= 0 or stop_loss <= 0:
                return error(400, "Bad Request", "Please provide positive inputs.")
            
            if entry_price == stop_loss or stop_loss > entry_price:
                return error(400, "Bad Request", "Entry price and stop loss do not tally.")
            
            symbol = request.form.get('symbol','').strip().upper()

            if not symbol: # if symbol field is empty
                return error(400, "Bad Request", "Please provide a symbol.")

            if not is_valid_ticker(symbol):
                return error(400, "Bad Request", "Please provide a valid symbol.")
            
            # doing calculation

            risk_per_share = entry_price - stop_loss
            max_dollar_risk = risk_per_trade / 100 * total
            recommended_size = math.floor(max_dollar_risk / risk_per_share)
            capital_required = recommended_size * entry_price
            portfolio_allocation = round(capital_required / total * 100, 2)

            return render_template(
                                    "sizing.html",
                                    total=total,
                                    cash=cash,
                                    risk_per_trade=risk_per_trade,
                                    symbol=symbol,
                                    entry_price=entry_price,
                                    stop_loss=stop_loss,
                                    risk_per_share=risk_per_share,
                                    max_dollar_risk=max_dollar_risk,
                                    recommended_size=recommended_size,
                                    capital_required=capital_required,
                                    portfolio_allocation=portfolio_allocation,
                                    )

        
        else: # if user tapped on navbar
            return render_template("sizing.html", total=total, recommended_size=-1)
    
    finally:
        connection.close()


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Quote stock price and other details"""

    user_id = session["user_id"]
    total = calculate_portfolio_value(user_id)["total_value"]

    return render_template('quote.html',total=total)


@app.route("/api/quote")
@login_required
def get_quote_html():
    """Returns stock quote when queried from html page"""

    symbol = request.args.get("symbol",'').strip().upper()

    if not is_valid_ticker(symbol):
        return error(400, "Bad Request", "Please provide a valid symbol.")

    data = get_quote(symbol)

    return jsonify(data)


@app.route("/api/history", methods=["GET"])
@login_required
def stock_history():
    """Obtains historical performance of a certain stock"""

    VALID_RANGES = {"1W", "1M", "6M", "1Y", "5Y"}
    range_param = request.args.get("range")
    if range_param not in VALID_RANGES:
        return error(400, "Bad Request", "Please provide a valid range.")

    symbol = request.args.get('symbol','').strip().upper()
    
    if not symbol: # if symbol field is empty
        return error(400, "Bad Request", "Please provide a symbol.")

    if not is_valid_ticker(symbol):
        return error(400, "Bad Request", "Please provide a valid symbol.")

    history = get_stock_history(symbol=symbol, range=range_param)

    return history


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    cursor, connection = db_connect()

    try: 
        if request.method == 'POST': # if the user is trying to buy shares
            symbol = request.form.get('symbol','').strip().upper()

            if not symbol: # if symbol field is empty
                return error(400, "Bad Request", "Please provide a symbol.")

            if not is_valid_ticker(symbol): # if symbol is not valid
                return error(400, "Bad Request", "Please provide a valid symbol.")

            data = get_quote(symbol)
            
            shares = request.form.get('shares') # amount of shares user wants to buy

            if not shares.isdigit():
                return error(400, "Bad Request", "Please provide a valid number of shares.")

            shares = int(shares) 

            if shares <= 0:
                return error(400, "Bad Request", "Please provide a positive number of shares.")
            
            user_id = session['user_id']
            cash_needed = data["current_price"] * shares
            current_cash = cursor.execute("select cash from users where id=?", (user_id,)).fetchone()["cash"]
            
            if cash_needed > current_cash: # check if user has sufficient cash
                return error(400, "Bad Request", "Insufficient cash.")
            
            # adds to database if transaction is valid
            cursor.execute("insert into transactions(user_id, symbol, shares, price) values(?, ?, ?, ?)", 
                            (session['user_id'], symbol, shares, data["current_price"]))
            connection.commit()

            current_cash -= cash_needed
            cursor.execute("update users set cash=? where id=?", (current_cash, user_id))
            connection.commit()

            flash(f"Successfully bought {shares} {'share' if shares == 1 else 'shares'} of {symbol}!", "success")
            return redirect('/') # returns user to homepage 
        
        else: # if user got through the navbar
            return render_template('buy.html')
        
    finally: 
        connection.close()


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    cursor, connection = db_connect()
    user_id = session['user_id']

    try:
        if request.method == 'POST':  # if the user is trying to buy shares
            symbol = request.form.get('symbol','').strip().upper()

            if not symbol:  # if symbol field is empty
                return error(400, "Bad Request", "Symbol field is empty.")

            if not is_valid_ticker(symbol): # if symbol is not valid
                return error(400, "Bad Request", "Please provide a valid symbol.")

            total_share = cursor.execute("select sum(shares) as total_share from transactions where user_id=? and symbol=?", (user_id, symbol)).fetchone()["total_share"]
            if total_share <= 0:  # if user somehow does not own any shares of the selected stock
                return error(400, "Bad Request", f"No shares of {symbol} owned.")

            price = get_quote(symbol)['current_price'] # current price of stock
            shares = request.form.get('shares')  # amount of shares user wants to sell

            if not shares.isdigit():
                return error(400, "Bad Request", "Amount of shares must be a whole integer.")

            shares = int(shares)

            if total_share < shares:
                return error(400, "Bad Request", "You cannot sell more shares than you own.")

            cash_gained = price * shares
            current_cash = cursor.execute("select cash from users where id=?", (user_id,)).fetchone()['cash']

            # adds to database if transaction is valid
            cursor.execute("insert into transactions(user_id, symbol, shares, price) values(?, ?, ?, ?)", (user_id, symbol, -1 * shares, price))
            connection.commit()
            current_cash += cash_gained
            cursor.execute("update users set cash=? where id=?", (current_cash, user_id))
            connection.commit()

            flash(f"Successfully sold {shares} {'share' if shares == 1 else 'shares'} of {symbol}!", "success")
            return redirect('/')  # returns user to homepage

        else:  # if user got through the navbar
            # returns a list containing dictionaries with symbol field that are distinct
            portfolio = cursor.execute("select distinct symbol from transactions where user_id=?", (user_id,)).fetchall()
            return render_template('sell.html', portfolio=portfolio)
    
    finally:
        connection.close()


@app.route("/cash", methods=["GET", "POST"])
@login_required
def add_cash():
    """Allows user to add cash to their account"""

    cursor, connection = db_connect()
    user_id = session['user_id']

    try:
        if request.method == "POST": # if user submitted through html form
            current_cash = cursor.execute("select cash from users where id=?", (user_id,)).fetchone()['cash']

            add_amount = request.form.get("add_amount")

            if not add_amount:
                return error(400, "Bad Request", "Cash field is empty.")
            
            if not add_amount.replace(".", "", 1).isdigit():
                    return error(400, "Bad Request", "Amount of cash must be a whole integer.")
            
            add_amount = int(add_amount)
            current_cash += add_amount
            cursor.execute("update users set cash=? where id=?", (current_cash, user_id))
            connection.commit()

            flash(f"Successfully added ${add_amount} cash!", "success")
            return redirect('/')
        
        else: # if user got through navbar
            current_cash = cursor.execute("select cash from users where id=?", (user_id,)).fetchone()['cash']
            return render_template('cash.html', current_cash=current_cash)

    finally:
        connection.close()


@app.route("/history")
@login_required
def history():
    """Displays transaction history"""

    cursor, connection = db_connect()

    try:
        user_id = session['user_id']

        # returns a list containing dictionaries with symbol, shares, price, and time fields
        data = cursor.execute("select symbol, shares, price, time from transactions where user_id=? order by time desc", (user_id,)).fetchall()
        portfolio = [dict(stock) for stock in data]

        for stock in portfolio:  # adds cash from each stock into total, 'stock' is a dictionary
            if stock['shares'] > 0:
                stock['type'] = "BUY"
            else:
                stock['type'] = "SELL"

        return render_template('history.html', portfolio=portfolio)
    
    finally:
        connection.close()



@app.route("/login", methods=["GET", "POST"])
def login():
    """Logs user in"""

    cursor, connection = db_connect()

    try:
        if request.method == "POST": # if user tries to login
            username = request.form.get("username")
            password = request.form.get("password")

            if not request.form.get("username"): # checks if user inputted a username
                return error(400, "Bad Request", "Please provide a username.")
            
            if not request.form.get("password"): # checks if user inputted a password
                return error(400, "Bad Request", "Please provide a password.")

            cursor.execute("select * from users where username=?", (username,))
            result = cursor.fetchall()

            if len(result) != 1:
                return error(400, "Bad Request", "Wrong username given.")

            cursor.execute("select hash from users where username=?", (username,))
            row = cursor.fetchone()
            if not check_password_hash(row["hash"], password): # if password does not match
                return error(400, "Bad Request", "Password does not match.")
            
            session['user_id'] = result[0]['id'] # if password matches, saves session
            return redirect("/") # brings user to homepage
            
        else: # if user presses login on navbar
            return render_template('login.html')
    
    finally:
        connection.close()
        

@app.route("/logout")
def logout():
    """Logs user out"""

    session.clear()
    return redirect('/login')


@app.route("/register", methods=["GET", "POST"])
def register():
    """Registers user"""

    cursor, connection = db_connect()

    try: 
        if request.method == "POST": # if user tries to register
            username = request.form.get('username')
            password = request.form.get('password')
            confirmation = request.form.get('confirmation')

            if not username or not password or not confirmation:
                return error(400, "Bad Request", "Fill in all fields.")
            
            if password != confirmation:
                return error(400, "Bad Request", "Passwords need to match.")

            try:
                cursor.execute("insert into users(username, hash) values(?, ?)", (username, generate_password_hash(password)))
            
            except sqlite3.IntegrityError: # if there is a duplicate username
                return error(400, "Bad Request", "Username is already taken.")
            
            connection.commit()
            # logs user in after they register
            session['user_id'] = cursor.lastrowid
            return redirect("/")

        else: # if user presses register on navbar
            return render_template("register.html")
        
    finally:
        connection.close()