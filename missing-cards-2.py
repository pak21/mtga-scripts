#!/usr/bin/env python3

import collections
import contextlib
import datetime
import os
import sys

import mysql.connector as mysql

DECK_SQL = '''
select deck_id, name
from decks
where
  source != 'Personal'
  and (deck_id < 95 or deck_id > 99) -- Ignore New Player Experience decks
  and name not like 'Artisan %'
  and name not like 'Casual %'
'''

CARD_SQL = '''
select cards.name, cards.mtga_id, cards.rarity, cards.types, max(sets.rotation_date), deck_cards.main, sum(collection.count)
from decks
join deck_cards on decks.deck_id = deck_cards.deck_id
join cards on deck_cards.name = cards.name
join sets on cards.set_id = sets.set_id
left join collection on cards.mtga_id = collection.mtga_id
where deck_cards.main > 0 and decks.deck_id = %s
group by cards.name
'''

ABILITIES_SQL = 'select ability_id from card_abilities where card_id = %s'

# The ID of the shockland "enters tapped or pay 2 life" ability
SHOCKLAND_ABILITY_ID = 90846

# The ID of the checkland "enters tapped unless you control an X or Y"
CHECKLAND_ABILITY_IDS = [1210, 91993, 92859, 92868, 92880, 99478, 99480, 99484, 99486, 99488]

# The generic "enters the battlefield tapped" ability
ENTERS_TAPPED_ABILITY_ID = 76735

BANNED_CARDS = [
    'Agent of Treachery',
    'Cauldron Familiar',
    'Field of the Dead',
    'Fires of Invention',
    'Growth Spiral',
    'Oko, Thief of Crowns',
    'Once Upon a Time',
    'Teferi, Time Raveler',
    'Veil of Summer',
    'Wilderness Reclamation'
]

def main():
    data = []
    is_dual = {}

    conn = mysql.connect(database='mtga', user='philip', password=os.environ['DATABASE_PASSWORD'])
    with contextlib.closing(conn.cursor()) as cursor:
        cursor.execute(DECK_SQL)
        for deck_id, deck_name in cursor.fetchall():

            cursor.execute(CARD_SQL, (deck_id,))
            cards = cursor.fetchall()

            needed_wildcards = collections.defaultdict(int)
            rotating_wildcards = collections.defaultdict(int)
            dual_lands = collections.defaultdict(int)

            banned = False
            for name, mtga_id, rarity, types, rotation_date, needed, owned in cards:
                if name in BANNED_CARDS:
                    banned = True

                owned = owned or 0
                if owned < needed:
                    needed_wildcards[rarity] += needed - owned
                    if rotation_date <= datetime.date(2019, 12, 31):
                        rotating_wildcards[rarity] += needed - owned

                    if 'Land' in types:
                        if mtga_id not in is_dual:
                            cursor.execute(ABILITIES_SQL, (mtga_id,))
                            abilities = [t[0] for t in cursor.fetchall()]
                            is_shockland = SHOCKLAND_ABILITY_ID in abilities
                            is_checkland = bool(set(abilities).intersection(CHECKLAND_ABILITY_IDS))
                            is_temple = name.startswith('Temple of ') and ENTERS_TAPPED_ABILITY_ID in abilities
                            is_triome = name.endswith(' Triome') and ENTERS_TAPPED_ABILITY_ID in abilities
                            is_dual[mtga_id] = is_shockland or is_checkland or is_temple or is_triome

                        if is_dual[mtga_id]:
                            dual_lands[rarity] += needed - owned

            if not banned and (rotating_wildcards['Rare'] + rotating_wildcards['Mythic Rare'] == 0):
                data.append((
                    needed_wildcards['Rare'] + needed_wildcards['Mythic Rare'],
                    dual_lands['Rare'] + dual_lands['Mythic Rare'],
                    deck_id,
                    deck_name))

    for missing_rares, dual_lands, deck_id, deck_name in sorted(data):
        print('Deck {} ({}) is missing {} rares, of {} are dual lands'.format(deck_name, deck_id, missing_rares, dual_lands))

if __name__ == '__main__':
    main()
