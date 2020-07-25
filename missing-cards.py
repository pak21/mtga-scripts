#!/usr/bin/env python3

import argparse
import collections

import mtga

CARD_SQL = '''
select cards.name, cards.rarity, deck_cards.main, sum(collection.count)
from decks
join deck_cards on decks.deck_id = deck_cards.deck_id
join cards on deck_cards.name = cards.name
left join collection on cards.mtga_id = collection.mtga_id
where deck_cards.main > 0 and decks.deck_id = %s
group by cards.name
'''

def get_data(cursor, deck):
    cursor.execute(CARD_SQL, (deck,))
    return cursor.fetchall()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--deck', type=int, help='Deck ID to query')
    args = parser.parse_args()

    conn = mtga.connect()
    cards = mtga.with_cursor(conn, lambda cursor: get_data(cursor, args.deck))

    needed_wildcards = collections.defaultdict(int)
    for name, rarity, needed, owned in cards:
        owned = owned or 0
        if owned < needed:
            print('You own {} copies of {} ({}) and need {}'.format(owned, name, rarity, needed))
            needed_wildcards[rarity] += needed - owned

    print()
    
    for rarity, count in needed_wildcards.items():
        print('{}: {}'.format(rarity, count))

if __name__ == '__main__':
    main()
