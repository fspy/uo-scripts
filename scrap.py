# pyright: reportCallIssue=false
import time

import API

# while not API.StopRequested:
#   API.UseSkill("Item Id")
#   API.WaitForTarget(timeout=1)
#   API.Target(0x40641413)
#   API.Pause(.85)

last = -1
while not API.StopRequested:
    # if API.Player.Mana >= 10 and not API.BuffExists("Lightning Strike"):
    #     API.CastSpell("Lightning Strike")
    #     API.Pause(0.3)
    if API.Player.Mana >= 10 and not API.BuffExists("Momentum Strike"):
        API.CastSpell("Momentum Strike")
        API.Pause(0.3)

    if time.perf_counter() - last > 20:
        last = time.perf_counter()
        API.CastSpell("Evasion")
        API.Pause(0.3)
