#!/usr/bin/env python3

import contextlib
import os

import mysql.connector as mysql
import pandas as pd

CARDS_SQL="select cards.name, cards.rarity, sum(collection.count) as n from collection join cards on collection.mtga_id = cards.mtga_id where cards.rarity != 'Basic' group by cards.name having n > 4 order by n desc, cards.name"

def main():
    conn = mysql.connect(database='mtga', user='philip', password=os.environ['DATABASE_PASSWORD'])
    with contextlib.closing(conn.cursor()) as cursor:
        cursor.execute(CARDS_SQL)
        cards = pd.DataFrame(cursor.fetchall(), columns=['name', 'rarity', 'count'])
        print(cards)

if __name__ == '__main__':
    main()
