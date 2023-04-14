"""
Stealing trainer using an item stack.
Rewritten to use a single stack of an item to steal from.

Original author and description:
# -----------------------------------------------
# Credits: McPaperstax
# Info: Training script prompts target for locked/secure container in player home. 
# Finds first item of appropriate weight to steal.
# -----------------------------------------------
"""

from AutoComplete import *

hue = 177
delay = 250  # for journal reads
verbose = False


def FindSteal(container, item_stack):
    """Find item to steal.
    args:
        container: Item `Serial` for the container.
        item_stack: Item `Serial` for the item stack.
    
    returns:
        the `Item` object for the found item.
        returns None if no item found.
    """
    container = Items.FindBySerial(container)

    if verbose:
        Misc.SendMessage('Container Name: {}'.format(container.Name), hue)
        Misc.SendMessage('Container Valid: {}'.format(container.IsContainer),
                         hue)

    foundItem = container.Contains.Find(lambda x: x.Serial == item_stack)

    if not foundItem:
        return None

    if verbose: Player.HeadMessage(hue, 'Found {}.'.format(foundItem.Name))
    return foundItem


def StealItem(container, item):
    """Performs the Stealing skill on the provided item.

    Attempts to steal `item`, checks the journal for either a success or
    failure message, then, if successful, returns the item to the container.

    args:
        container: Item `Serial` for the container.
        item: the `Item` object for the item to be stolen.
    """
    Journal.Clear()
    Misc.Pause(delay)

    Player.UseSkill('Stealing')
    Target.WaitForTarget(2000, True)
    Target.TargetExecute(item)
    Misc.Pause(delay)

    if Journal.SearchByName('You fail to steal the item.', 'System'):
        # Steal fail pause and retry
        if verbose: Misc.SendMessage('Steal Fail.', hue)
        pass
    elif Journal.SearchByName('You successfully steal the item.', 'System'):
        # Steal succeed, return item to container
        if verbose: Misc.SendMessage('Steal Success.', hue)
        player_item = Player.Backpack.Contains.Find(
            lambda x: x.ItemID == item.ItemID)
        Items.Move(player_item.Serial, container, -1)

    Misc.Pause(10000)
    if verbose: Misc.SendMessage('Next Attempt', hue)


# -----------------------------------
# Main Script Execution Begins Here
# -----------------------------------

item_stack = Target.PromptTarget(
    'Select the item stack you want to steal from.', hue)
container = Items.FindBySerial(item_stack).RootContainer
if verbose:
    Misc.SendMessage('{} -> {}'.format(hex(item_stack), hex(container)), hue)

while Player.GetRealSkillValue('Stealing') < Player.GetSkillCap('Stealing'):
    currentSkill = Player.GetRealSkillValue('Stealing')

    if currentSkill < 40:
        Player.HeadMessage(
            'Train or Soulstone stealing skill to 40 or higher.', hue)
    else:
        item = FindSteal(container, item_stack)

    if not item:
        break

    StealItem(container, item)

Misc.SendMessage('Stealing script has stopped running.', hue)