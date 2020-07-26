#!/usr/bin/env python3

import mtga

CARDS_SQL="""
select cards.name, cards.rarity, sum(collection.count) as n
from collection
join cards on collection.mtga_id = cards.mtga_id
where cards.rarity != 'Basic'
group by cards.name
having n > 4
order by n desc, cards.name
"""

def main():
    print(mtga.with_cursor(mtga.connect(), mtga.get_dataframe(CARDS_SQL, ['name', 'rarity', 'count'])))

if __name__ == '__main__':
    main()
