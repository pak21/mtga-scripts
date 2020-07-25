import contextlib
import os

import mysql.connector as mysql

def connect():
    return mysql.connect(database='mtga', user='philip', password=os.environ['DATABASE_PASSWORD'])

def with_cursor(conn, callback):
    with contextlib.closing(conn.cursor()) as cursor:
        return callback(cursor)
