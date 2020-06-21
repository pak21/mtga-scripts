import re

class ChannelFireballNormalizer():
    # Common CFB errors
    CFB_ERRORS = {
        'Panoptic Mirror': 'Opt',
        'Quenchable Fire': 'Quench',
        'Sarkhan the Mad': 'Sarkhan the Masterless',
        'Inescapable Brute': 'Inescapable Blaze',
    }

    def normalize(self, name):
        # Convert "Forest (335)" or similar to just "Forest"
        name = re.sub(r' \([0-9]+\)$', '', name)

        # Convert split cards to their canonical form
        if '/' in name and not ' // ' in name:
            name = name.replace('/', ' // ')

        # Suffixes
        name = re.sub(r' - Foil', '', name)
        name = re.sub(r'(- )?(Buy-a-Box Promo|Brawl Deck Exclusive)', '', name)
        name = re.sub(r' - Borderless', '', name)
        name = re.sub(r' - Collector Pack Exclusive', '', name)
        name = re.sub(r' - Promo Pack', '', name)
        name = re.sub(r' - Theme Booster Exclusive', '', name)
        name = re.sub(r' - Planeswalker Deck Exclusive', '', name)
        name = re.sub(r' - Welcome Deck Exclusive', '', name)
        name = re.sub(r' - Showcase', '', name)
        name = re.sub(r' - Extended Art', '', name)

        # Set IDs and numbers
        name = re.sub(r'\(...\) \d+$', '', name)

        # Fancy apostrophes
        name = name.replace('’', "'")

        if name in self.CFB_ERRORS:
            name = self.CFB_ERRORS[name]

        yield name

        # Try the front-side only of dual faced cards
        if ' // ' in name:
            name = re.sub(r' // .*', '', name)
            yield name
