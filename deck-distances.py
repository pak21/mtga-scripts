#!/usr/bin/env python3

import contextlib
import os
import sys

import mysql.connector as mysql

DECKS_SQL = '''
select deck_id from decks
'''

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

def get_distance(cursor, id1, id2):
    cursor.execute(DIFF_SQL, (id2, id1, id1, id2))
    diffs = cursor.fetchall()

    total_diff = 0
    for name, count_a, count_b in diffs:
        if count_a > count_b:
            total_diff += (count_a - count_b)

    return total_diff

def main():
    conn = mysql.connect(database='mtga', user='philip', password=os.environ['DATABASE_PASSWORD'])
    with contextlib.closing(conn.cursor()) as cursor:
        cursor.execute(DECKS_SQL)
        decks = [row[0] for row in cursor.fetchall()]
        print(decks)

        for i in range(len(decks)):
            print(i)
            for j in range(i+1, len(decks)):
                d1, d2 = decks[i], decks[j]
                if d2 < d1:
                    d2, d1 = d1, d2

                diff = get_distance(cursor, d1, d2)
                cursor.execute('insert into deck_distances set deck_id1 = %s, deck_id2 = %s, distance = %s', (d1, d2, diff))

        conn.commit()

if __name__ == '__main__':
    main()
