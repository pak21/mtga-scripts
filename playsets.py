#!/usr/bin/env python3

from datetime import date

import mtga

PLAYSETS_SQL="""
select cards.set_id, sets.release_date, cards.rarity, count(*), coalesce(sum(collection.count = 4), 0)
from cards
join sets on cards.set_id = sets.set_id
left join collection on cards.mtga_id = collection.mtga_id
where
  sets.max_booster_set_number > 0 and
  cards.set_number <= sets.max_booster_set_number and
  cards.rarity != 'Basic'
group by cards.set_id, cards.rarity
order by sets.release_date, cards.rarity
"""

def main():
    playsets = mtga.with_cursor(mtga.connect(), mtga.get_dataframe(PLAYSETS_SQL, ['set', 'release_date', 'rarity', 'cards', 'playsets']))

    playsets = playsets[(playsets.rarity == 'Uncommon') & (playsets.release_date > date(2019, 7, 12))]
    playsets = playsets[['cards', 'playsets']]

    totals = playsets.sum()
    ratio = totals.playsets / totals.cards
    print('You own {} out of {} playsets, a ratio of {:.2f}'.format(int(totals.playsets), int(totals.cards), ratio))

    uncommon_worth = ratio * (3/1000) * 3
    print('That makes an uncommon ICR worth {:.3f} wildcards, or {:.0f} gold'.format(uncommon_worth, uncommon_worth * 6000))

if __name__ == '__main__':
    main()
