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

        decks = tree.xpath('//div[@class="wp-cfb-streamdecker"]')
        for deck in decks:
            title = re.sub(' - .*', '', deck.find('h3').text)
            print(title)

            arena_buttons = deck.xpath('.//div[@class="icon mtga-icon "]')
            if not arena_buttons:
                print("Couldn't find Arena download button, skipping...\n")
                continue

            arena_button = arena_buttons[0]
            onclick_text = arena_button.get('onclick')
            onclick_text = re.sub(r'^copy\(\'', '', onclick_text)
            onclick_text = re.sub(r'\'\)$', '', onclick_text)
            onclick_text = onclick_text.replace('\\r\\n', '\n')
            onclick_text = onclick_text.replace('\\\'', '\'')

            cursor.execute('insert into decks set name = %s, source = %s', (title, args.url))

            cursor.execute('select last_insert_id()')
            deck_id = cursor.fetchall()[0][0]
            print('Importing deck {}'.format(deck_id))

            deck = parse_deck(onclick_text)

            cards = collections.defaultdict(lambda: (0, 0))
            for name, counts in deck.items():
                cards[name] = tuple(sum(i) for i in zip(cards[name], counts))

            for name, counts in cards.items():
                cursor.execute('insert into deck_cards set deck_id = %s, name = %s, main = %s, sideboard = %s', (deck_id, name, *counts))

        conn.commit()

if __name__ == '__main__':
    main()
