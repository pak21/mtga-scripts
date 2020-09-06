#!/usr/bin/env python3

import argparse

import mtga

CARDS_SQL="""
select cards.name, cards.rarity, count(distinct set_id) as n
from cards
where
  cards.rarity in ('Rare', 'Mythic Rare') and
  cards.set_id not in ('G18', 'ANA', 'ANB', 'SLD') and
  ({} or cards.set_id != 'JMP')
group by cards.name
having n > 1
"""

def main():
    parser = argparse.ArgumentParser()
    parser.set_defaults(include_jmp=False)
    parser.add_argument('-j', '--include-jmp', action='store_true')
    args = parser.parse_args()

    query = CARDS_SQL.format(args.include_jmp)
    conn = mtga.connect()
    cards = mtga.with_cursor(conn, mtga.get_dataframe(query, ['name', 'rarity', 'sets']))
    print(cards)

if __name__ == '__main__':
    main()
