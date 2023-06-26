from AutoComplete import *

item = Target.PromptTarget('Target item to organize:', 1151)

if not item:
    import sys
    sys.exit()

item = Items.FindBySerial(item)
cont = item.Container
items = Items.FindAllByID(item.ItemID, -1, cont, True)
# x, y = 44, 96 # 44, 64
x, y = item.Position.X, item.Position.Y
for i in sorted(items, key=lambda x: x.Name):
    print(i.Name)
    Items.Move(i.Serial, cont, 0, x, y)
    x += 8  # 10
    if x > 156:
        x = 44  # item.Position.X # 44
        y += 16  # 20
    Misc.Pause(666)

Misc.SendMessage('Done organizing!', 1151)
