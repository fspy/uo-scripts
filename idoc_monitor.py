# check if house is still up
# make sure you're hidden while waiting!!!
# will stop beeping once you move (out of hiding)

from AutoComplete import *

house_serial = Target.PromptTarget("Click the house sign!", 61)
Timer.Create('Hiding', 1)
while Items.FindBySerial(house_serial):
    Misc.Pause(200)
    if Player.Visible and not Timer.Check('Hiding'):
        Player.UseSkill('Hiding')
        Timer.Create('Hiding', 10500)
else:
    while not Player.Visible:
        Misc.Beep()
        Misc.Pause(200)