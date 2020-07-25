#!/usr/bin/env python3

import contextlib
import os

import mysql.connector as mysql
import pandas as pd

CARDS_SQL="select cards.name, cards.rarity, count(distinct set_id) as n from cards where cards.rarity in ('Rare', 'Mythic Rare') and cards.set_id not in ('G18', 'ANA', 'SLD') group by cards.name having n > 1"

def main():
    conn = mysql.connect(database='mtga', user='philip', password=os.environ['DATABASE_PASSWORD'])
    with contextlib.closing(conn.cursor()) as cursor:
        cursor.execute(CARDS_SQL)
        cards = pd.DataFrame(cursor.fetchall(), columns=['name', 'rarity', 'sets']).set_index('name')
        print(cards)

if __name__ == '__main__':
    main()
