#!/usr/bin/python3

import contextlib
import os

import mtga.set_data
import mysql.connector as mysql

COLOR_MAPPING = {
    'W': 'White',
    'U': 'Blue',
    'B': 'Black',
    'R': 'Red',
    'G': 'Green'
}

ADD_CARD_SQL="""
insert into cards
set
  mtga_id = %s,
  name = %s,
  set_id = %s,
  set_number = %s,
  collectible = %s,
  rarity = %s,
  artist_id = %s,
  types = %s,
  power = %s,
  toughness = %s,
  color_identity = %s
"""

def main():
    conn = mysql.connect(database='mtga', user='philip', password=os.environ['DATABASE_PASSWORD'])
    with contextlib.closing(conn.cursor()) as cursor:
        cursor.execute('select id from abilities')
        known_abilities = set([row[0] for row in cursor.fetchall()])

        for ability_id, text in [(ability_id, text) for ability_id, text in mtga.set_data.all_mtga_abilities.items() if ability_id not in known_abilities]:
            cursor.execute('insert into abilities set id = %s, ability = %s', (ability_id, text))

        cursor.execute('select name from card_subtypes')
        known_subtypes = set([row[0] for row in cursor.fetchall()])

        for card in mtga.set_data.all_mtga_cards.cards:
            for subtype in [subtype for subtype in card.sub_types.split() if subtype not in known_subtypes]:
                cursor.execute('insert into card_subtypes set name = %s', (subtype,))
                known_subtypes.add(subtype)

        cursor.execute('select id, name from card_subtypes')
        subtypes = {name: subtype_id for subtype_id, name in cursor.fetchall()}

        cursor.execute('select name from artists')
        known_artists = set([row[0] for row in cursor.fetchall()])

        for card in mtga.set_data.all_mtga_cards.cards:
            if card.artist not in known_artists:
                print('Adding {}'.format(card.artist))
                cursor.execute('insert into artists set name = %s', (card.artist,))
                known_artists.add(card.artist)

        cursor.execute('select id, name from artists')
        artists = {name: id for id, name in cursor.fetchall()}

        cursor.execute('select mtga_id from cards')
        known_cards = set([row[0] for row in cursor.fetchall()])

        for card in [card for card in mtga.set_data.all_mtga_cards.cards if card.mtga_id not in known_cards]:
            types = ','.join([t for t in card.card_type.split(' ') if t != ''])
            colors = ','.join([COLOR_MAPPING[c] for c in card.color_identity])
            artist_id = artists[card.artist]
            print(card.mtga_id, card.pretty_name, card.set, card.rarity, types, colors)
            cursor.execute(
                ADD_CARD_SQL,
                (
                    card.mtga_id, card.pretty_name, card.set, card.set_number, card.collectible, card.rarity,
                    artist_id, types, card.power, card.toughness, colors
                )
            )

            card_subtypes = card.sub_types.split()
            for t in card_subtypes:
                cursor.execute('insert into card_subtypes_link set card_id = %s, subtype_id = %s', (card.mtga_id, subtypes[t]))

            for ability_id in card.abilities:
                cursor.execute('insert into card_abilities set card_id = %s, ability_id = %s', (card.mtga_id, ability_id))

            for style in card.styles:
                cursor.execute('insert into card_styles_link set card_id = %s, style_id = %s', (card.mtga_id, style))

    conn.commit()

if __name__ == '__main__':
    main()
