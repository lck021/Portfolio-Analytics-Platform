import os

import sqlite3
from flask import Flask, flash, redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import *
from api import *

# Configure application
app = Flask(__name__)

# Configure cookies
app.config["SECRET_KEY"] = "abcde"

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
    """Show portfolio value"""

    user_id = session['user_id']
    cursor, connection = db_connect()

    try:
        # returns a list containing dictionaries with symbol and total_share fields
        portfolio = cursor.execute("select symbol, sum(shares) as total_shares from transactions where user_id=? group by symbol", (user_id,)).fetchall()
        
        current_cash = cursor.execute("select cash from users where id=?", (user_id,)).fetchone()["cash"]
        total = current_cash

        for stock in portfolio: # adds cash from each stock into total, 'stock' is a dictionary
            current_price = get_quote(stock['symbol'])["current_price"]
            total += round(stock['total_shares'] * current_price, 2)
        
        return render_template('dashboard.html', total_value=total)
    
    finally:
        connection.close()


@app.route('/breakdown')
@login_required
def breakdown():
    """Displays portfolio breakdown"""

    user_id = session['user_id']
    cursor, connection = db_connect()

    try:
        # returns a list containing dictionaries with symbol and total_share fields
        portfolio = cursor.execute("select symbol, sum(shares) as total_shares from transactions where user_id=? group by symbol", (user_id,)).fetchall()
        
        current_cash = cursor.execute("select cash from users where id=?", (user_id,)).fetchone()["cash"]
        total = current_cash

        for stock in portfolio: # adds cash from each stock into total, 'stock' is a dictionary
            current_price = get_quote(stock['symbol'])["current_price"]
            stock['price'] = current_price
            stock['total'] = round(stock['total_shares'] * current_price, 2)
            total += stock['total']
        
        return render_template('breakdown.html', portfolio=portfolio, current_cash=current_cash, total=total)
    
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

