#!/usr/bin/env python3

import contextlib
import os

import matplotlib.pyplot as plt
import mysql.connector as mysql
import networkx as nx
import numpy as np
import pandas as pd
import sklearn.cluster

COLOR_SQL_TEMPLATE = '''
select
  sum(deck_cards.main),
  cards.color_identity
from deck_cards
join cards on cards.mtga_id = (select mtga_id from cards where name = deck_cards.name limit 1)
where
  deck_id in ({})
  and deck_cards.main > 0
group by deck_cards.name
'''

def get_cluster_color(df, cursor, cluster):
    cluster_decks = ','.join([str(d) for d in df[df.cluster == cluster].deck_id])
    sql = COLOR_SQL_TEMPLATE.format(cluster_decks)
    cursor.execute(sql)

    color_counts = {'White': 0, 'Blue': 0, 'Black': 0, 'Red': 0, 'Green': 0}
    total_cards = 0
    for count, color_identity in cursor.fetchall():
        total_cards += count
        for color in color_identity:
            color_counts[color] += count

    color_fractions = {k: float(v/total_cards) for k, v in color_counts.items()}
    return (color_fractions['Red'], color_fractions['Green'], color_fractions['Blue'])

def update_annot(df, scatter, annot, ind):
    first = ind['ind'][0]
    annot.xy = scatter.get_offsets()[first]
    text = '{} ({})'.format(*df.iloc[first][['deck', 'cluster']])
    annot.set_text(text)

def hover(event, df, fig, scatter, ax, annot):
    vis = annot.get_visible()
    if event.inaxes == ax:
        cont, ind = scatter.contains(event)
        if cont:
            update_annot(df, scatter, annot, ind)
            annot.set_visible(True)
            fig.canvas.draw_idle()
        else:
            if vis:
                annot.set_visible(False)
                fig.canvas.draw_idle()

def main():
    np.random.seed(42)

    conn = mysql.connect(database='mtga', user='philip', password=os.environ['DATABASE_PASSWORD'])
    with contextlib.closing(conn.cursor()) as cursor:
        cursor.execute('select deck_id, name from decks')
        decks = pd.DataFrame(cursor.fetchall(), columns=['deck_id', 'deck'])

        cursor.execute('select deck_id1, deck_id2, distance from deck_distances')
        rows = np.array(cursor.fetchall())

    ids = set(rows[:,0]).union(set(rows[:,1]))
    id_to_deck_mapping = {point_id: deck_id for point_id, deck_id in enumerate(ids)}
    deck_to_id_mapping = {deck_id: point_id for point_id, deck_id in enumerate(ids)}

    distances = np.zeros((len(ids), len(ids)))
    for deck_id1, deck_id2, distance in rows:
        weight = (60 - distance)**2
        point_id1 = deck_to_id_mapping[deck_id1]
        point_id2 = deck_to_id_mapping[deck_id2]
        distances[point_id1, point_id2] = weight
        distances[point_id2, point_id1] = weight

    G = nx.Graph(distances)
    layout_dict = nx.spring_layout(G)
    layout = pd.DataFrame(
        [(id_to_deck_mapping[k], *v) for k, v in layout_dict.items()],
        columns=['deck_id', 'x', 'y']
    )

    df = pd.merge(decks, layout, on='deck_id')

    dbscan = sklearn.cluster.DBSCAN(eps=0.1).fit(df[['x', 'y']].values)
    df['cluster'] = dbscan.labels_
    df['marker'] = ['.' if cluster != -1 else 'x' for cluster in df.cluster]

    with contextlib.closing(conn.cursor()) as cursor:
        df['color'] = df.cluster.apply(lambda cluster: get_cluster_color(df, cursor, cluster) if cluster != -1 else (0.8, 0.8, 0.8))

    fig, ax = plt.subplots()
    scatter = plt.scatter(df.x, df.y, color=df.color.values)

    annot = ax.annotate('', xy=(0, 0), xytext=(20, 20), textcoords='offset points', bbox=dict(boxstyle='round', fc='w'), arrowprops=dict(arrowstyle='->'))
    annot.set_visible(False)

    fig.canvas.mpl_connect('motion_notify_event', lambda event: hover(event, df, fig, scatter, ax, annot))

    plt.show()

if __name__ == '__main__':
    main()
