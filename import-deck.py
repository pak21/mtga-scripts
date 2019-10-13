#!/usr/bin/env python3

import argparse
import collections
import contextlib
import os
import re

import mysql.connector as mysql

class NameNormalizer():
    def normalize(self, name):
        # Convert "Forest (335)" or similar to just "Forest"
        name = re.sub(r' \([0-9]+\)$', '', name)

        # Convert split cards to their canonical form
        if '/' in name and not ' // ' in name:
            name = name.replace('/', ' // ')

        # Box promos
        name = re.sub(r' (- Foil )?(- )?(Buy-a-Box Promo|Brawl Deck Exclusive)', '', name)

        # Borderless
        name = re.sub(r' - Borderless', '', name)

        # Arena export metadata
        name = re.sub(r' \([A-Z0-9]{2,3}\) [0-9]+$', '', name)

        yield name

        # Try the front-side only of dual faced cards
        if ' // ' in name:
            name = re.sub(r' // .*', '', name)
            yield name

def get_argparse_parser():
    parser = argparse.ArgumentParser(description='Insert a deck')
    parser.add_argument('-n', '--name', help='Deck name', required=True)
    parser.add_argument('-s', '--source', help='Deck source')
    parser.add_argument('-d', '--deck', help='Deck file', required=True)
    return parser

def parse_arguments():
    parser = get_argparse_parser()
    return parser.parse_args()

def read_deck(filename):
    cards = collections.defaultdict(lambda: [0, 0])
    with open(filename, 'r') as f:
        sideboard = 0
        for l in f:
            line = l.rstrip()
            if line == '' or line.startswith('//'):
                continue
            if line == 'Sideboard':
                sideboard = 1
                continue
            count, name = line.split(' ', 1)
            count = int(count)
            cards[name][sideboard] += count

    return cards

def validate_name(conn, normalized):
    with contextlib.closing(conn.cursor()) as cursor:
        cursor.execute('select mtga_id from cards where name = %s', (normalized,))
        cardids = cursor.fetchall()
        return cardids != []

def main():
    args = parse_arguments()

    normalizer = NameNormalizer()

    deck = read_deck(args.deck)

    conn = mysql.connect(database='mtga', user='philip', password=os.environ['DATABASE_PASSWORD'])

    with contextlib.closing(conn.cursor()) as cursor:
        cursor.execute('insert into decks set name = %s, source = %s', (args.name, args.source))

        cursor.execute('select last_insert_id()')
        deck_id = cursor.fetchall()[0][0]

        cards = collections.defaultdict(lambda: (0, 0))
        for name, counts in deck.items():
            good_name = None
            for normalized in normalizer.normalize(name):
                if validate_name(conn, normalized):
                    good_name = normalized
                    break
            if not good_name:
                raise Exception('Card {} unknown'.format(name))
            cards[good_name] = tuple(sum(i) for i in zip(cards[good_name], counts))

        for name, counts in cards.items():
            cursor.execute('insert into deck_cards set deck_id = %s, name = %s, main = %s, sideboard = %s', (deck_id, name, *counts))

    conn.commit()

if __name__ == "__main__":
    main()
