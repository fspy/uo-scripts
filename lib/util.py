from AutoComplete import *


def head_prompt(msg, c=55):
    """Shows a head message on target prompt, instead of bottom left."""
    Player.HeadMessage(c, msg)
    return Target.PromptTarget('')


def safe_cast(spell, target=None, wait=3000):
    """Tries to safely cast a spell.
    
    If we're paralyzed or currently waiting for a target, skip casting.
    It can also be used as a "sphere style" type of casting, if no target
    is provided: Asks for a target first, casting after.
    """
    if not target:
        target = Target.PromptTarget('select a target')
    if Player.Paralized or Target.HasTarget():
        return False
    Spells.Cast(spell)
    Target.WaitForTarget(wait)
    Target.TargetExecute(target)
    return True