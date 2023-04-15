from System.Collections.Generic import List
from System import Int32
from AutoComplete import *
from lib.util import ItemFilter

cotton_id = 0x0DF9
spool_id = 0x0FA0
spinning_wheel_ids = [0x1019]
loom_ids = [0x105F, 0x1060]

swf = ItemFilter(spinning_wheel_ids, range_max=2, on_ground=1)
lf = ItemFilter(loom_ids, max_range=2, on_ground=1)

while True:
    cotton = Items.FindByID(cotton_id, -1, Player.Backpack.Serial)
    wheel = swf.get('Nearest')
    if cotton and wheel:
        Items.UseItem(cotton)
        Target.WaitForTarget(3000)
        Target.TargetExecute(wheel)
    Misc.Pause(200)

    spool = Items.FindByID(spool_id, -1, Player.Backpack.Serial)
    loom = lf.get('Nearest')
    if spool and loom:
        for _ in range(spool.Amount):
            Items.UseItem(spool)
            Target.WaitForTarget(3000)
            Target.TargetExecute(loom)
            Misc.Pause(50)