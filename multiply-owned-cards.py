#!/usr/bin/env python3

import pandas as pd

import mtga

CARDS_SQL="select cards.name, cards.rarity, sum(collection.count) as n from collection join cards on collection.mtga_id = cards.mtga_id where cards.rarity != 'Basic' group by cards.name having n > 4 order by n desc, cards.name"

def get_data(cursor):
    cursor.execute(CARDS_SQL)
    return cursor.fetchall()

def main():
    conn = mtga.connect()
    cards = pd.DataFrame(mtga.with_cursor(conn, get_data), columns=['name', 'rarity', 'count'])
    print(cards)

if __name__ == '__main__':
    main()
