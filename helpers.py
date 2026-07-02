from functools import wraps
import sqlite3

from flask import redirect, render_template, render_template_string, request, session

def login_required(func) -> None:
    """Directs user to login if they have not, else process the request"""

    @wraps(func)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return func(*args, **kwargs)
    
    return decorated_function

def error(code, title, message):
    return render_template('error.html', code=code, title=title, message=message)

def db_connect():
    connection = sqlite3.connect("platform.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    return cursor, connection