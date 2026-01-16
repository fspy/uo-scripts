import API

target = API.RequestTarget(5)
while API.FindMobile(target):
    API.CastSpell("Death Ray")
    API.WaitForTarget("any", 5)
    API.Target(API.Found)  # pyright: ignore
    API.Pause(0.3)
    if not API.InJournalAny(["resist", "fizzles"]):
        break
