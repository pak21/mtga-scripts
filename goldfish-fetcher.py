#!/usr/bin/env python3

import enum

import argparse
import collections
import contextlib
import os
import re
from lxml import html
import mysql.connector as mysql
import requests

EXPORT_URL_TEMPLATE = 'https://www.mtggoldfish.com/deck/arena_download/{}'

class ParserState(enum.Enum):
    DECK = enum.auto()
    SIDEBOARD = enum.auto()
    COMPANION = enum.auto()

PARSER_STATE_STRINGS = {
    'Deck': ParserState.DECK,
    'Sideboard': ParserState.SIDEBOARD,
    'Companion': ParserState.COMPANION
}

def parse_line(old_state, line):
    print(line)

    match = re.match(r'^([0-9]+) (.*)', line)
    count, name = match.groups()

    return old_state, (name, old_state, int(count))

def parse_deck(deck_text):
    cards = collections.defaultdict(lambda: [0, 0])
    state = ParserState.DECK
    companion = None

    for line in deck_text.splitlines():
        if line == '':
            continue

        if line in PARSER_STATE_STRINGS:
            state = PARSER_STATE_STRINGS[line]
            continue

        match = re.match(r'^([0-9]+) (.*)', line)
        count, name = match.groups()

        if state == ParserState.DECK:
            cards[name][0] = int(count)
        elif state == ParserState.SIDEBOARD:
            cards[name][1] = int(count)
        elif state == ParserState.COMPANION:
            companion = name

    return cards, companion

def main():
    conn = mysql.connect(database='mtga', user='philip', password=os.environ['DATABASE_PASSWORD'])

    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--url', required=True)
    args = parser.parse_args()

    page = requests.get(args.url)
    tree = html.fromstring(page.content)

    decks = tree.xpath('//ins[@class="widget-deck-placeholder"]')

    with contextlib.closing(conn.cursor()) as cursor:
        for deck_content in decks:
            cursor.execute('insert into decks set name = "Imported Deck", source = %s', (args.url,))

            cursor.execute('select last_insert_id()')
            deck_id = cursor.fetchall()[0][0]
            print('Importing deck {}'.format(deck_id))

            export_url = EXPORT_URL_TEMPLATE.format(deck_content.get('data-id'))
            print('Fetching deck from {}'.format(export_url))
            export_page = requests.get(export_url)
            export_tree = html.fromstring(export_page.content)

            deck_text = export_tree.xpath('//textarea[@class="copy-paste-box"]')[0].text
            deck, companion = parse_deck(deck_text)

            cards = collections.defaultdict(lambda: (0, 0))
            for name, counts in deck.items():
                cards[name] = tuple(sum(i) for i in zip(cards[name], counts))

            for name, counts in cards.items():
                is_companion = name == companion
                cursor.execute('insert into deck_cards set deck_id = %s, name = %s, main = %s, sideboard = %s, is_companion = %s', (deck_id, name, *counts, is_companion))

        conn.commit()

if __name__ == '__main__':
    main()
