import re

class NameNormalizer():
    def normalize(self, name):
        # Convert "Forest (335)" or similar to just "Forest"
        name = re.sub(r' \([0-9]+\)$', '', name)

        # Convert split cards to their canonical form
        if '/' in name and not ' // ' in name:
            name = name.replace('/', ' // ')

        # Box promos
        name = re.sub(r' (- Foil )?(- )?(Buy-a-Box Promo|Brawl Deck Exclusive)', '', name)

        # Borderless
        name = re.sub(r' - Borderless', '', name)

        # Arena export metadata
        name = re.sub(r' \([A-Z0-9]{2,3}\) [0-9]+$', '', name)

        yield name

        # Try the front-side only of dual faced cards
        if ' // ' in name:
            name = re.sub(r' // .*', '', name)
            yield name
