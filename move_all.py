source = Target.PromptTarget('Source container:')
destination = Target.PromptTarget('Destination container:')

def get_items(cont):
    items = []
    for i in Items.FindBySerial(cont).Contains:
        items.append(i)
        if i.IsContainer:
            items.extend(get_items(i))
    return items

Items.WaitForContents(source, 2000)
items = get_items(source)

for i in items:
    Items.Move(i, destination, 0)
    Misc.Pause(620)