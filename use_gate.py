import API

for g in [0x0F6C, 0x4BCB]:
    if API.FindType(g, range=1):
        API.HeadMsg("Using Gate", API.Found)
        API.UseObject(API.Found)
        break
