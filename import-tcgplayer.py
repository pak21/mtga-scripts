#!/usr/bin/env python3

import argparse
import collections
import contextlib
import os
import re

import mysql.connector as mysql

def parse_arguments():
    parser = argparse.ArgumentParser(description='Insert a deck')
    parser.add_argument('-s', '--source', help='Deck source', required=True)
    parser.add_argument('-d', '--deck', help='Deck file', required=True)
    return parser.parse_args()

def read_deck(filename):
    cards = collections.defaultdict(lambda: [0, 0])
    with open(filename, 'r') as f:
        sideboard = 0
        deck_name = None
        for l in f:
            line = l.rstrip()
            if line == '':
                continue

            if deck_name is None:
                deck_name = line
                continue

            count, name = line.split(' ', 1)

            if count == 'Sideboard':
                sideboard = 1
                continue

            try:
                count = int(count)
            except ValueError:
                continue

            cards[name][sideboard] += count

    return deck_name, cards

def validate_name(conn, normalized):
    with contextlib.closing(conn.cursor()) as cursor:
        cursor.execute('select mtga_id from cards where name = %s', (normalized,))
        cardids = cursor.fetchall()
        return cardids != []

def main():
    args = parse_arguments()

    deck_name, deck = read_deck(args.deck)

    conn = mysql.connect(database='mtga', user='philip', password=os.environ['DATABASE_PASSWORD'])

    with contextlib.closing(conn.cursor()) as cursor:
        cursor.execute('insert into decks set name = %s, source = %s', (deck_name, args.source))

        cursor.execute('select last_insert_id()')
        deck_id = cursor.fetchall()[0][0]

        cards = collections.defaultdict(lambda: (0, 0))
        for name, counts in deck.items():
            cards[name] = tuple(sum(i) for i in zip(cards[name], counts))

        for name, counts in cards.items():
            cursor.execute('insert into deck_cards set deck_id = %s, name = %s, main = %s, sideboard = %s', (deck_id, name, *counts))

    conn.commit()

if __name__ == "__main__":
    main()
