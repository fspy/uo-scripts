"""
Navrey Pillars Auto-Clicker

This script will attempt to use a nearby pillar in Navrey's arena.
The order of the pillars is randomized per boss spawn!
"""

from datetime import datetime

from AutoComplete import *

nf = Mobiles.Filter()
nf.Name = 'Navrey Night-Eyes'
nf.Bodies.Add(0x02DF)


def click_stone():
    stone = Items.FindByID(0x03bf, 0, -1, 2)
    if not stone: return
    Items.UseItem(stone)
    Items.Message(stone, 1266, '* Clicked! *')
    Misc.Pause(625)


def wait_respawn():
    killtime = datetime.now()
    Player.HeadMessage(1153,
                       f'Navery DEAD at {killtime.strftime("%H:%M:%S")}!')
    Misc.Pause(1000)
    while not Mobiles.ApplyFilter(nf):
        Misc.Pause(1000)
    else:
        respawn = (datetime.now() - killtime).total_seconds()
        m, s = int(respawn // 60), int(respawn % 60)
        Player.HeadMessage(1153, f'Navrey Spawned! ({m:02}:{s:02})')
        for _ in range(8):
            Misc.Beep()
            Misc.Pause(33)


while True:
    click_stone()

    # navrey corpse
    if Items.FindByID(0x2006, 0, -1, -1):
        wait_respawn()

    Misc.Pause(50)