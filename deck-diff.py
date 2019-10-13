#!/usr/bin/env python3

import contextlib
import os
import sys

import mysql.connector as mysql

DIFF_SQL = '''
  select a.name, a.main as a, coalesce(b.main, 0) as b
  from deck_cards as a
  left join deck_cards as b on a.name = b.name and b.deck_id = %s
  where a.deck_id = %s and a.main > 0 and (a.main != b.main or b.main is null)
union
  select b.name, coalesce(a.main, 0), b.main from deck_cards as a
  right join deck_cards as b on a.name = b.name and a.deck_id = %s
  where b.deck_id = %s and b.main > 0 and (a.main != b.main or a.main is null)
'''

def main():
    conn = mysql.connect(database='mtga', user='philip', password=os.environ['DATABASE_PASSWORD'])
    with contextlib.closing(conn.cursor()) as cursor:
        cursor.execute('select deck_id, name from decks where deck_id in (%s, %s)', (sys.argv[1], sys.argv[2]))
        deck_names = {k: v for k, v in cursor.fetchall()}
        deck1 = deck_names[int(sys.argv[1])]
        deck2 = deck_names[int(sys.argv[2])]
        print('Comparing {} and {}'.format(deck1, deck2))

        cursor.execute(DIFF_SQL, (sys.argv[2], sys.argv[1], sys.argv[1], sys.argv[2]))
        diffs = cursor.fetchall()

        total_diff = 0
        for name, count_a, count_b in diffs:
            if count_a > count_b:
                total_diff += (count_a - count_b)
            print(name, count_a, count_b)

        print('{} cards differ'.format(total_diff))

if __name__ == '__main__':
    main()
