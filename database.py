import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

def db_connect():
    """Connects to sqlite database"""

    connection = sqlite3.connect(os.environ.get("DB_PATH"))
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    return cursor, connection