import sqlite3

def db_connect():
    """Connects to sqlite database"""

    connection = sqlite3.connect("platform.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    return cursor, connection