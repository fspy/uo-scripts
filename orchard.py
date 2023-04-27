# Apple name: An Enchanted Apple of *
# Tree name: Cypress Tree

ACTION_DELAY = 1000 # pause between checks and actions
SHOW_TICK = True # show ... over player head
CHECKED_COLOR = 0x084c # blue
TARGET_COLOR = 0x0845 # red

# Apple object properties for locating in the backpack
# (probably do not carry a regular apple here, it has the same appearance)
APPLE_ID = 0x09D0
APPLE_COLOR = 0x0000

VIRTUES = [
    'compassion', 
    'honesty', 
    'honor', 
    'humility',
    'justice', 
    'sacrafice', #sic (it is misspelled in the game)
    'spirituality',
    'valor',
]

ANTIVIRTUES = [
    'despise',
    'deceit',
    'shame',
    'pride',
    'wrong',
    'covetous',
    'hythloth',
    'destard',
]


# Tree data is saved here. Serials in their own set for convenience.
trees = {} 
checked_tree_serials = set()


# Return the opposing match for any virtue/antivirtue.
def get_opposite(word):
    if word in VIRTUES:
        return ANTIVIRTUES[VIRTUES.index(word)]
    elif word in ANTIVIRTUES:
        return VIRTUES[ANTIVIRTUES.index(word)]

    # If we get here, things went off the rails somehow.
    Player.HeadMessage(1100, 'Lookup failed: {0}!'.format(word))
    return None

    
# Return the first tree within one tile, if there is one.
def get_tree():
    obj_filter = Items.Filter()
    obj_filter.Enabled = True
    obj_filter.Name = "Cypress Tree"
    obj_filter.RangeMax = 1
    objs = Items.ApplyFilter(obj_filter)

    if objs:
        return objs[0]
    return None


# Return virtue apple from backpack.
def get_apple():
    return Items.FindByID(APPLE_ID, APPLE_COLOR, Player.Backpack.Serial)
    

# Apple picking loop
while True:
    # Find a tree within 1 tile.
    tree = get_tree()
    
    # Pick an apple if this is a tree that has not been tried already.
    if tree and tree.Serial not in checked_tree_serials:
        Player.HeadMessage(1100, 'Picking apple...')       
        Items.UseItem(tree)
        Misc.Pause(ACTION_DELAY)
        
        apple = get_apple()
        
        if apple:
            # Get the opposite virtue/antivirtue for our apple.
            virt = apple.Name.split(' ')[-1].lower()
            opposite = get_opposite(virt)

            # Save tree info and recolor it as already-checked.            
            trees[virt] = tree
            Items.SetColor(tree.Serial, CHECKED_COLOR)
            
            if opposite in trees.keys():
                # Found a match! Notify, and target-color the opposing tree.
                Player.HeadMessage(1100, '!! {0} => {1} !!'.format(virt, opposite))
                opposite_tree = trees[opposite]
                Items.SetColor(opposite_tree.Serial, TARGET_COLOR)
            else:
                # No match. Indicate how many trees have been checked so far.
                Player.HeadMessage(1100, '?? GUESS ({0}) ??'.format(len(trees)))
                
            checked_tree_serials.add(tree.Serial)
        else:
            # Something went wrong finding the apple in our backpack.
            Player.HeadMessage(1100, 'Failed to find apple!')
            
        
    Misc.Pause(ACTION_DELAY)
    if SHOW_TICK:
        Player.HeadMessage(1100, '...')
