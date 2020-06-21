#!/usr/bin/env python3

import argparse
import contextlib
import os

import mysql.connector as mysql

def main():
    parser = argparse.ArgumentParser(description='Find decks containing a given card')
    parser.add_argument('-c', '--card', help='Card to look up', required=True)
    args = parser.parse_args()

    conn = mysql.connect(database='mtga', user='philip', password=os.environ['DATABASE_PASSWORD'])
    print('{} appears in the following decks:\n'.format(args.card))
    with contextlib.closing(conn.cursor()) as cursor:
        cursor.execute('select decks.deck_id, decks.name, deck_cards.main, deck_cards.sideboard from decks join deck_cards on decks.deck_id = deck_cards.deck_id where deck_cards.name = %s', (args.card,))
        decks = cursor.fetchall()
        for deck_id, name, main, sideboard in decks:
            print('{} ({}) - {} ({})'.format(name, deck_id, main, sideboard))

if __name__ == '__main__':
    main()
