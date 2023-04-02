from AutoComplete import *
import re

debug = True


class Query:
    Weapon = re.compile('weapon damage', re.IGNORECASE)
    Gargoyle = re.compile('gargoyles only', re.IGNORECASE)
    Unravel = re.compile('(magic item)$', re.IGNORECASE)
    # Unravel = re.compile('(lesser artifact|magic item)$', re.IGNORECASE)

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
            if sum(1 for prop in item.Properties if re.search(query, prop.ToString())) >= count:
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
            score = Query.item_score(item, weights)
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
            dest = container_prompt('Target destination container')
        for item in items:
            if debug:
                Misc.SendMessage('Moving {}'.format(item.Name))
            Items.Move(item.Serial, dest, -1)
            self.rm(item)
            Misc.Pause(620)


def container_prompt(msg, c=55):
    Player.HeadMessage(c, msg)
    return Target.PromptTarget('')


CONTAINER_WEAPON = 0x40722114
CONTAINER_UNRAVEL = 0x40722B66
CONTAINER_GARGOYLE = 0x402E19F0

chests = {
    0.33: 0x40316502,
    0.27: 0x4072208F,
    0.22: 0x40722B9C,
    0.18: 0x40722B88,
    0.15: 0x40722C94
}


q = Query(source=container_prompt('Target source container'))

if debug:
    print('MOVING UNRAVEL')
q.move_all(q.query_prop(q.Unravel), CONTAINER_UNRAVEL)

if debug:
    print('MOVING GARGOYLE')
q.move_all(q.query_prop(q.Gargoyle), CONTAINER_GARGOYLE)

if debug:
    print('MOVING WEAPON')
q.move_all(q.query_prop(q.Weapon), CONTAINER_WEAPON)

weights = {
    'lower reagent cost': [4, 25],
    'lower mana cost': [6, 10],
    'mana regeneration': [5, 4],
    'mana increase':  [3, 10],
    'intelligence bonus': [3, 10],
    'resist': [4, 35],
    'faster casting': [8, 4],
    'faster cast recovery': [10, 6]
}

for (weight, container) in sorted(chests.items(), reverse=True, key=lambda x: float(x[0])):
    if debug:
        Misc.SendMessage('MOVING SCORE >= {}'.format(weight), 1150)
    q.move_all(q.query_weighted(float(weight), weights), container)


Misc.SendMessage("Done sorting items!", 65)
