#!/usr/bin/env python3

import contextlib
import os

import mysql.connector as mysql
import pandas as pd

# Finds all lands with more than one "{T}: add {<colour>}" ability - the five
# of these have IDs 1001 to 1005
IMPLICIT_DUALS_QUERY="select mtga_id from cards join card_abilities on cards.mtga_id = card_abilities.card_id where cards.types = 'Land' and card_abilities.ability_id >= 1001 and card_abilities.ability_id <= 1005 group by cards.mtga_id having count(*) >= 2"

# Finds all lands with a "{T}: add {<colour>} or {<colour>} ability"; there are
# 10 of these abilities for each of the colour pairs, hardcoded in the 'in'
# clause here
EXPLICIT_DUALS_QUERY="select mtga_id from cards join card_abilities on cards.mtga_id = card_abilities.card_id where cards.types = 'Land' and card_abilities.ability_id in (1039, 1131, 1167, 1203, 1209, 1211, 4247, 4407, 18472, 18504)"

CARD_COUNTS_TEMPLATE="""
select
  min(cards.mtga_id),
  cards.name,
  coalesce(sum(collection.count), 0),
  max(sets.rotation_date) > now()
from cards
left join collection on cards.mtga_id = collection.mtga_id
join sets on cards.set_id = sets.set_id
where cards.mtga_id in ({})
group by cards.name
"""

CARD_ABILITIES_TEMPLATE="""
select
  cards.name,
  shock.ability_id is not null,
  tap.ability_id is not null,
  `check`.ability_id is not null,
  gate.subtype_id is not null,
  scry.ability_id is not null,
  gain.ability_id is not null
from cards
left join card_abilities as shock on cards.mtga_id = shock.card_id and shock.ability_id = 90846
left join card_abilities as tap on cards.mtga_id = tap.card_id and tap.ability_id = 76735
left join card_abilities as `check` on cards.mtga_id = `check`.card_id and `check`.ability_id in (1210, 91993, 92859, 92868, 92880, 99478, 99480, 99484, 99486, 99488)
left join card_subtypes_link as gate on cards.mtga_id = gate.card_id and gate.subtype_id = 58
left join card_abilities as scry on cards.mtga_id = scry.card_id and scry.ability_id = 91717
left join card_abilities as gain on cards.mtga_id = gain.card_id and gain.ability_id = 90050
where cards.mtga_id in ({})
"""

def calculate_type(card):
    if card.is_shock:
        return 'Shockland'

    if card.is_check:
        return 'Checkland'

    if card.is_gate:
        return 'Gate'

    if card.is_gain:
        return 'Gainland'

    if card.is_scry:
        return 'Scryland'

    if card.is_tap:
        return 'Tapland'

    return 'Original Dual'

def main():
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)

    conn = mysql.connect(database='mtga', user='philip', password=os.environ['DATABASE_PASSWORD'])
    with contextlib.closing(conn.cursor()) as cursor:
        cursor.execute(IMPLICIT_DUALS_QUERY)
        implicit_duals = cursor.fetchall()

        cursor.execute(EXPLICIT_DUALS_QUERY)
        explicit_duals = cursor.fetchall()

        duals_sql = ', '.join([str(t[0]) for t in implicit_duals + explicit_duals])
        cards_query = CARD_COUNTS_TEMPLATE.format(duals_sql)
        cursor.execute(cards_query)
        duals = pd.DataFrame(cursor.fetchall(), columns=['mtga_id', 'name', 'count', 'in_standard']).set_index('name')
        duals.in_standard = duals.in_standard.astype(bool)

        duals_sql2 = ', '.join([str(i) for i in duals.mtga_id])
        abilities_query = CARD_ABILITIES_TEMPLATE.format(duals_sql2)
        cursor.execute(abilities_query)

        dual_types = pd.DataFrame(cursor.fetchall(), columns=['name', 'is_shock', 'is_tap', 'is_check', 'is_gate', 'is_scry', 'is_gain']).set_index('name')

        dual_types['type'] = dual_types.apply(calculate_type, axis=1)
        dual_types = dual_types[['type']]

        combined = duals[['count', 'in_standard']].join(dual_types)
        print(combined[combined.in_standard & (combined['count'] < 4)])

if __name__ == '__main__':
    main()