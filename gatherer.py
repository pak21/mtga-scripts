#!/usr/bin/env python3

import argparse
import contextlib
import os

import mysql.connector as mysql

SUBTYPES_SQL='''
select card_subtypes.name
from cards
join card_subtypes_link on cards.mtga_id = card_subtypes_link.card_id
join card_subtypes on card_subtypes_link.subtype_id = card_subtypes.id
where cards.mtga_id = %s
'''

ABILITIES_SQL='''
select ability
from cards
join card_abilities on cards.mtga_id = card_abilities.card_id
join abilities on card_abilities.ability_id = abilities.id
where cards.mtga_id = %s
'''

def main():
    parser = argparse.ArgumentParser(description='Look up MtG (Arena) card')
    parser.add_argument('-c', '--card', help='Card to look up', required=True)
    args = parser.parse_args()

    conn = mysql.connect(database='mtga', user='philip', password=os.environ['DATABASE_PASSWORD'])
    with contextlib.closing(conn.cursor()) as cursor:
        cursor.execute(
            'select cards.mtga_id, cards.name, cards.rarity, cards.types, cards.power, cards.toughness, cards.set_id, cards.color_identity from cards where name like %s',
            ('%{}%'.format(args.card),)
        )
        for mtga_id, name, rarity, types, power, toughness, set_id, colors in cursor.fetchall():
            types_string = ', '.join(types)
            colors_string = ', '.join(colors)

            cursor.execute(SUBTYPES_SQL, (mtga_id,))
            subtypes = ', '.join([t[0] for t in cursor.fetchall()])

            print('{} ({}) {}/{} - {} ({}) ({}) - {}'.format(name, set_id, power, toughness, types_string, subtypes, colors_string, rarity))
            print()

            cursor.execute(ABILITIES_SQL, (mtga_id,))
            for ability, in cursor.fetchall():
                print('* {}'.format(ability))

            print()

if __name__ == '__main__':
    main()
