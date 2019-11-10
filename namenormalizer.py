import re

class ChannelFireballNormalizer():
    def normalize(self, name):
        # Convert "Forest (335)" or similar to just "Forest"
        name = re.sub(r' \([0-9]+\)$', '', name)

        # Convert split cards to their canonical form
        if '/' in name and not ' // ' in name:
            name = name.replace('/', ' // ')

        # Suffixes
        name = re.sub(r' (- Foil )?(- )?(Buy-a-Box Promo|Brawl Deck Exclusive)', '', name)
        name = re.sub(r' - Borderless', '', name)
        name = re.sub(r' - Collector Pack Exclusive', '', name)

        # Fancy apostrophes
        name = name.replace('’', "'")

        yield name

        # Try the front-side only of dual faced cards
        if ' // ' in name:
            name = re.sub(r' // .*', '', name)
            yield name
