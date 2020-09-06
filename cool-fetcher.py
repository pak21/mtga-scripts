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

        match = re.match(r'^([0-9]+) (.*) \([A-Z0-9]{2,3}\) [0-9]+$', line)
        count, name = match.groups()
        cards[name][sideboard] = int(count)

    return cards

def main():
    conn = mysql.connect(database='mtga', user='philip', password=os.environ['DATABASE_PASSWORD'])

    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--url', required=True)
    args = parser.parse_args()

    headers = {'User-Agent': 'Mozilla'}
    page = requests.get(args.url, headers=headers)
    tree = html.fromstring(page.content)

    with contextlib.closing(conn.cursor()) as cursor:

        for deck_div in tree.xpath('//div[@class="gm-deck row"]'):
            deck_title_element = deck_div.xpath('.//h4')[0]
            deck_title = re.sub(r'\|.*', '', deck_title_element.text).strip()

            deck_button = deck_div.xpath('.//a[@class="copydecklist"][button/img]')[0]
            deck_text = deck_button.get('data-text').replace('|', '\n').replace('~', '')

            cursor.execute('insert into decks set name = %s, source = %s', (deck_title, args.url))

            cursor.execute('select last_insert_id()')
            deck_id = cursor.fetchall()[0][0]
            print('Importing deck {}: {}'.format(deck_id, deck_title))

            deck = parse_deck(deck_text)

            cards = collections.defaultdict(lambda: (0, 0))
            for name, counts in deck.items():
                cards[name] = tuple(sum(i) for i in zip(cards[name], counts))

            for name, counts in cards.items():
                if name == 'Lurrus of the Dream Den':
                    name = 'Lurrus of the Dream-Den'
                cursor.execute('insert into deck_cards set deck_id = %s, name = %s, main = %s, sideboard = %s', (deck_id, name, *counts))

        conn.commit()

if __name__ == '__main__':
    main()
