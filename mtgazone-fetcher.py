#!/usr/bin/env python3

import argparse
import collections
import contextlib
import os
import re

from lxml import html
import mysql.connector as mysql
import requests

def parse_deck(deck_text):
    cards = collections.defaultdict(lambda: [0, 0])
    sideboard = 0

    for line in deck_text.splitlines():
        if line == 'Deck':
            continue

        if line == '' or line == 'Sideboard':
            sideboard = 1
            continue

        print(line)
        match = re.match(r'^([0-9]+) (.*)', line)
        count, name = match.groups()
        cards[name][sideboard] = int(count)

    return cards

def main():
    conn = mysql.connect(database='mtga', user='philip', password=os.environ['DATABASE_PASSWORD'])

    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--url', required=True)
    args = parser.parse_args()

    page = requests.get(args.url)
    tree = html.fromstring(page.content)

    export_button = tree.xpath('//div[@role="button"]')[0]
    onclick_text = export_button.get('onclick')
    onclick_text = re.sub(r'^copy\(\'', '', onclick_text)
    onclick_text = re.sub(r'\'\)$', '', onclick_text)
    onclick_text = onclick_text.replace('\\r\\n', '\n')
    onclick_text = onclick_text.replace('\\\'', '\'')

    deck = parse_deck(onclick_text)

    with contextlib.closing(conn.cursor()) as cursor:
        cursor.execute('insert into decks set name = "Imported Deck", source = %s', (args.url,))

        cursor.execute('select last_insert_id()')
        deck_id = cursor.fetchall()[0][0]
        print('Importing deck {}'.format(deck_id))

        cards = collections.defaultdict(lambda: (0, 0))
        for name, counts in deck.items():
            cards[name] = tuple(sum(i) for i in zip(cards[name], counts))

        for name, counts in cards.items():
            cursor.execute('insert into deck_cards set deck_id = %s, name = %s, main = %s, sideboard = %s', (deck_id, name, *counts))

        conn.commit()

if __name__ == '__main__':
    main()
