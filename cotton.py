from System.Collections.Generic import List
from System import Int32

cotton_id = 0x0DF9
spool_id = 0x0FA0
spinning_wheel_ids = [0x1019]
loom_ids = [0x105F, 0x1060]

swf = Items.Filter()
swf.Graphics = List[Int32](spinning_wheel_ids)
swf.RangeMax = 2
swf.OnGround = 1

lf = Items.Filter()
lf.Graphics = List[Int32](loom_ids)
lf.RangeMax = 2
lf.OnGround = 1

while True:
    cotton = Items.FindByID(cotton_id, -1, Player.Backpack.Serial)
    wheel = Items.Select(Items.ApplyFilter(swf), 'Nearest')
    if cotton and wheel:
        Items.UseItem(cotton)
        Target.WaitForTarget(3000)
        Target.TargetExecute(wheel)
    Misc.Pause(200)
    
    spool = Items.FindByID(spool_id, -1, Player.Backpack.Serial)
    loom = Items.Select(Items.ApplyFilter(lf), 'Nearest')
    if spool and loom:
        for _ in range(spool.Amount):    
            Items.UseItem(spool)
            Target.WaitForTarget(3000)
            Target.TargetExecute(loom)
            Misc.Pause(50)