#!/usr/bin/env python3

import collections
import itertools
from operator import itemgetter

import graphviz

import mtga

NAMES_SQL = "select distinct(cards.name) from cards where cards.rarity != 'Token'"

def get_names(cursor):
    cursor.execute(NAMES_SQL)
    return [r[0] for r in cursor.fetchall()]

def main():
    names = mtga.with_cursor(mtga.connect(), get_names)
    foo = [(name, name.split(' ')) for name in names]
    bar = [(name, words[0], words[-1]) for name, words in foo if len(words) > 1]

    a = sorted(bar, key=itemgetter(1))
    b = collections.defaultdict(list, {k: [x for x, _, _ in list(v)] for k, v in itertools.groupby(a, itemgetter(1))})

    dot = graphviz.Digraph()
    for name, _, last in bar:
        dot.node(name, name)
        for c in b[last]:
            dot.edge(name, c)

    print(dot.source)

if __name__ == '__main__':
    main()
