import contextlib
import os

import mysql.connector as mysql
import pandas as pd

def connect():
    return mysql.connect(database='mtga', user='philip', password=os.environ['DATABASE_PASSWORD'])

def with_cursor(conn, callback):
    with contextlib.closing(conn.cursor()) as cursor:
        return callback(cursor)

def _get_dataframe(cursor, sql, column_names):
    cursor.execute(sql)
    return pd.DataFrame(cursor.fetchall(), columns=column_names)

def get_dataframe(sql, column_names):
    return lambda cursor: _get_dataframe(cursor, sql, column_names)
