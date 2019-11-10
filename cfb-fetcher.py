#!/usr/bin/env python3

import argparse
import collections
import contextlib
import os

from lxml import html
import mysql.connector as mysql
import requests

import namenormalizer

def parse_deck(deck_text):
    cards = collections.defaultdict(lambda: [0, 0])
    sideboard = 0

    for line in deck_text.splitlines():
        if line == '':
            continue

        if line == 'Sideboard':
            sideboard = 1
            continue

        count_str, name = line.split(' ', 1)
        cards[name][sideboard] += int(count_str)

    return cards

def validate_name(cursor, name):
    cursor.execute('select 1 from cards where name = %s', (name,))
    return cursor.fetchall()

def main():
    conn = mysql.connect(database='mtga', user='philip', password=os.environ['DATABASE_PASSWORD'])

    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--url', required=True)
    args = parser.parse_args()

    headers = {'User-Agent': 'Mozilla'}
    page = requests.get(args.url, headers=headers)
    tree = html.fromstring(page.content)

    normalizer = namenormalizer.ChannelFireballNormalizer()

    with contextlib.closing(conn.cursor()) as cursor:

        decks = tree.xpath('//div[@class="plain-text-decklist"]/pre')
        for deck_content in decks:
            cursor.execute('insert into decks set name = "Imported Deck", source = %s', (args.url,))

            cursor.execute('select last_insert_id()')
            deck_id = cursor.fetchall()[0][0]
            print('Importing deck {}'.format(deck_id))

            deck = parse_deck(deck_content.text)

            cards = collections.defaultdict(lambda: (0, 0))
            for name, counts in deck.items():
                good_name = None
                for normalized in normalizer.normalize(name):
                    if validate_name(cursor, normalized):
                        good_name = normalized
                        break
                if not good_name:
                    raise Exception("Couldn't match name {}".format(name))

                cards[good_name] = tuple(sum(i) for i in zip(cards[good_name], counts))

            for name, counts in cards.items():
                cursor.execute('insert into deck_cards set deck_id = %s, name = %s, main = %s, sideboard = %s', (deck_id, name, *counts))

        conn.commit()

if __name__ == '__main__':
    main()
