from datetime import datetime

from AutoComplete import *

from lib.util import Hue

stone_id = 0x0ED4
governor_elect_id = 0x119C12
governor_id = 0x119C13
trade_deal_id = 0x119C0B

towns = [
    "Britain", "Jhelom", "New Magincia", "Minoc", "Moonglow", "Skara Brae",
    "Trinsic", "Vesper", "Yew"
]

trade_deals = {
    "Guild of Arcane Arts": "+5% Spell Damage Increase",
    "Society of Clothiers": "+1% Resist bump to all resists",
    "Bardic Collegium": "+1 Faster Casting",
    "Order of Engineers": "+3 Dexterity Bonus",
    "Guild of Healers": "5% Bandage Healing Bonus",
    "Maritime Guild": "+2 Hit Point Regeneration",
    "Merchant's Association": "+2 Mana Regeneration",
    "Mining Cooperative": "+3 Strength Bonus",
    "League of Rangers": "+3 Intelligence Bonus",
    "Guild of Assassins": "+5% Swing Speed Increase",
    "Warrior's Guild": "+5% Hit Chance Increase"
}

towns_checked = 0
town_deals = {}


def get_prop_by_number(props, number):
    try:
        res = next(filter(lambda x: x.Number == number, props))
        return res.ToString()
    except:
        return None


Misc.ClearIgnore()
while towns_checked < 9:

    stone = Items.FindByID(stone_id, -1, -1, True)
    if not stone:
        Misc.Pause(600)
        continue

    Items.WaitForProps(stone, 600)
    town = next(filter(lambda t: t in stone.Name, towns))
    Player.HeadMessage(Hue.Cyan,
                       'Found {} stone! Getting data...'.format(town))

    gov_prop = get_prop_by_number(stone.Properties, governor_id)
    if not gov_prop:
        gov_prop = get_prop_by_number(stone.Properties, governor_elect_id)
    has_gov = "Pending King's Choice" not in gov_prop

    deal_prop = get_prop_by_number(stone.Properties, trade_deal_id)
    deal_prop = deal_prop.replace('Current Trade Deal: ', '')
    trade_deal = trade_deals.get(deal_prop)

    town_deals[town] = trade_deal or 'None ({})'.format(
        gov_prop if has_gov else "no governor")

    towns_checked += 1
    Misc.Pause(600)
    Misc.IgnoreObject(stone)
    Player.HeadMessage(
        Hue.Cyan,
        'Stored data for {} stone! Waiting for next town... ({})'.format(
            town, towns_checked))

Player.HeadMessage(
    Hue.Green,
    "Gathered data for all towns! Summary stored in 'trade_deals.txt'")

with open('trade_deals.txt', 'w+') as f:
    f.write('# Trade Deals Summary - {}\n'.format(datetime.utcnow()))
    for town, deal in town_deals.items():
        f.write('- **{}**: {}\n'.format(town, deal))
    f.close()
