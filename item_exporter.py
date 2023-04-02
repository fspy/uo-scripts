from datetime import datetime
from AutoComplete import *
from collections import defaultdict
from lib.colors import colors

import clr

clr.AddReference('System.Drawing')
from System.Drawing.Imaging import *


def gen_html(i, img_file):
    div = '<div class="item"><img src="{}"/><p>{} ({} - hue {})</p></div>\n'
    return div.format(img_file, i.Name.strip(), hex(i.ItemID), i.Hue)


def main(f):
    cont = Target.PromptTarget('Target container', colors['yellow'])
    if not cont:
        return Misc.SendMessage('Unable to retrieve container', colors['purple'])

    cont_data = Items.FindBySerial(cont)
    if not cont_data:
        return Misc.SendMessage("Error retrieving container's items",
                                colors['purple'])

    item_data = defaultdict(list)
    for item in cont_data.Contains:
        item_data[item.ItemID].append(item)

    for (id, items) in sorted(item_data.items(), key=lambda x: x[0]):
        items.sort(key=lambda x: x.Name)
        for i in items:
            img_file = '{}-{}.png'.format(id, i.Hue)
            i.Image.Save('./Data/Items/{}'.format(img_file),
                         ImageFormat.Png)
            f.write(gen_html(i, img_file))


now = datetime.now().strftime('%Y%m%d%H%M')
with open('./Data/Items/Export-{}.html'.format(now), 'w') as f:
    f.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Item Export {}</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
<div class="items">
""".format(now))

    main(f)

    f.write("""</div>
</body>
</html>""")
