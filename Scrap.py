# pyright: reportCallIssue=false

import API


def getMobByGraphic():
    mob = API.NearestMobile([API.Notoriety.Criminal], 12)
    return mob or None

def forensic():
    API.UseSkill("forensic")
    API.WaitForTarget()
    API.Target(API.LastTargetSerial)
    API.Pause(1)


def herding():
    mob = getMobByGraphic()
    while mob:
        API.UseObject(API.FindType(0x0E81, API.Player.Backpack))
        API.WaitForTarget(timeout=2)
        API.Target(mob)
        API.WaitForTarget(timeout=2)
        API.Target(API.Player)
        mob = getMobByGraphic()
        API.Pause(0.5)


while not API.StopRequested:
    #herding()
    forensic()