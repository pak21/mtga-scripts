#!/usr/bin/env python3

import argparse

import mtga

SQL = """
select decks.deck_id, decks.name, deck_cards.main, deck_cards.sideboard
from decks
join deck_cards on decks.deck_id = deck_cards.deck_id
where deck_cards.name = %s
"""

def get_data(cursor, card):
    cursor.execute(SQL, (card,))
    return cursor.fetchall()

def main():
    parser = argparse.ArgumentParser(description='Find decks containing a given card')
    parser.add_argument('-c', '--card', help='Card to look up', required=True)
    args = parser.parse_args()

    decks = mtga.with_cursor(mtga.connect(), lambda cursor: get_data(cursor, args.card))

    print('{} appears in the following decks:\n'.format(args.card))
    for deck_id, name, main, sideboard in decks:
        print('{} ({}) - {} ({})'.format(name, deck_id, main, sideboard))

if __name__ == '__main__':
    main()
