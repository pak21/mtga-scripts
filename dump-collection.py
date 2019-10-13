#!/usr/bin/env python3

import contextlib
import os

import mysql.connector as mysql

def main():
    conn = mysql.connect(database='mtga', user='philip', password=os.environ['DATABASE_PASSWORD'])
    with contextlib.closing(conn.cursor()) as cursor:
        cursor.execute('select cards.name, cards.rarity, cards.set_id, cards.mtga_id, collection.count from collection left join cards on collection.mtga_id = cards.mtga_id order by cards.name, collection.mtga_id')
        for row in cursor.fetchall():
            print(*row)

if __name__ == '__main__':
    main()
