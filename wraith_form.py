from AutoComplete import *


def wraith_form():
    current = Player.Body

    def dress(list):
        Dress.ChangeList(list)
        Dress.DressFStart()
        while Dress.DressStatus():
            Misc.Pause(50)

    dress('wraith')
    Spells.Cast('Wraith Form')
    while Player.Body == current:
        Misc.Pause(50)
    dress('sdi')


wraith_form()
