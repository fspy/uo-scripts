current_form = Player.Body
while True:
    Spells.Cast('Wraith Form')
    Misc.Pause(1025)
    if current_form != Player.Body:
        break