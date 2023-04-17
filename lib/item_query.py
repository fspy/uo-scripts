# ItemQuery parses items and allows you to move them based on regular
# expressions. It also has a function that sorts items by a specified
# weight dictionary, calculating a score, normalized to [0,1[.

# It can query for specific named properties, their amount, how many,
# their name, and weights.

from AutoComplete import *
from .util import head_prompt
import re

debug = False


class ItemQuery:
    # some default queries
    MinorMagic = re.compile('^minor magic item$', re.IGNORECASE)
    LesserMagic = re.compile('^lesser magic item$', re.IGNORECASE)
    GreaterMagic = re.compile('^greater magic item$', re.IGNORECASE)
    MajorMagic = re.compile('^major magic item$', re.IGNORECASE)
    LesserArtifact = re.compile('^lesser artifact$', re.IGNORECASE)
    GreaterArtifact = re.compile('^greater artifact$', re.IGNORECASE)
    MajorArtifact = re.compile('^major artifact$', re.IGNORECASE)
    LegendaryArtifact = re.compile('^legendary artifact$', re.IGNORECASE)

    Weapon = re.compile('weapon damage', re.IGNORECASE)
    Gargoyle = re.compile('gargoyles only', re.IGNORECASE)
    Unravel = re.compile('(magic item)$', re.IGNORECASE)

    def __init__(self, source):
        Items.WaitForContents(source, 3000)
        self.items = Items.FindBySerial(source).Contains

    def rm(self, item):
        for i in self.items:
            if i.Serial == item.Serial:
                self.items.Remove(i)
                return

    def _search(self, item, query):
        return any(query.search(prop.ToString()) for prop in item.Properties)

    def query_prop(self, query, name=False):
        if name:
            result = filter(lambda item: query.search(item.Name), self.items)
        else:
            result = filter(lambda item: self._search(item, query), self.items)
        return list(result)

    def query_prop_count(self, query, count=1):
        result = []
        for item in self.items:
            if sum(1 for prop in item.Properties
                   if re.search(query, prop.ToString())) >= count:
                result.append(item)
        return result

    def query_prop_amount(self, query, min=60):
        result = []
        for item in self.items:
            total = 0
            for prop in item.Properties:
                match = re.search(query, prop.ToString())
                if match:
                    total += int(match.group(1))
            if total >= min:
                result.append(item)
        return result

    def query_weighted(self, min, weights):
        """retrieves items with a minimum score.

        applies `item_score` to all items using `weights`.
        returns only items with a `min` minimum score.

        args:
            min: the minimum score (0-1) an item should have.
            weights: a dictionary of prop weights: 
                example = { 
                    propName: [weight, maxVal],
                    'Faster Casting': [2.6, 2],
                }

        returns:
            result: the list of items with score above `min`.
        """
        result = []
        for item in self.items:
            score = ItemQuery.item_score(item, weights)
            if score >= min:
                result.append(item)
        return result

    @classmethod
    def item_score(cls, item, weights):
        """scores an item according to provided weights.

        searches through `weights` using regex and extracting the prop values,
        then takes the weighted average normalized to [0, 1].

        args:
            item: an Item, from the Razor Enhanced API.
            weights: a dictionary of property names and their weights / maximum.
                example:
                weights = {
                    'Lower Reagent Cost': [2.6, 25],
                }
                TODO: possibly make weights its own class? have to add all mods.

        returns:
            score: the properties from `weights` scored and normalized to [0, 1].
        """
        score = 0.0
        sum_weights = sum(x[0] for x in weights.values())
        for prop in item.Properties:
            for mod, (weight, max) in weights.items():
                match = re.search(r"{} \b(\d+)\b".format(mod), prop.ToString())
                if not match:
                    continue
                score += float(match.group(1)) / max * weight
        return score / sum_weights

    def move_all(self, items, dest=None):
        """moves all provided items to destination container.

        args:
            items: list of items to be moved.
            dest: the destination container. asks if empty.
        """
        if not dest:
            dest = head_prompt('Target destination container')
        for item in items:
            if debug:
                Misc.SendMessage('Moving {}'.format(item.Name))
            Items.Move(item.Serial, dest, -1)
            self.rm(item)
            Misc.Pause(620)