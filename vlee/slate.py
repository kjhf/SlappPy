import requests
import json
from typing import Optional, Set

from vlee import battlefyToolkit

ORG_SLUGS = list({
    "lsi",
    "splatoon-sea-level-up-tournament-organization",
    "torneo-star-oni",
    "splatcol",
    "shadow-sirens",
    "extrafest",
    "vroom-vroom-veemo",
    "area-cup",
    "inkling-performance-labs",
    "notorious-network-community-league",
    "splashdown Saturdays",
    "tbd-thursdays",
    "sitback-saturdays",
    "boilermaker-booyah",
    "ci-studios",
    "altaira",
    "technorganic-esport-league",
    "inkloning",
    "off-the-dial",
    "swift-second-saturdays",
    "küki-tournaments",
    "deca-tower",
    "fresh-start-cup",
    "casual-friday",
    "circuit-down-under",
    "headspace-horoscopes",
    "aygi-gaming",
    "squid-spawning-grounds",
    "woomy-games-inc",
    "splatendo-competitive™",
    "gamesetmatch",
    "callisto",
    "eki",
    "nebula-splatoon-2",
    "xtreme-tourneys",
    "good-guys-win",
    "asquidmin",
    "armorless-adventures",
    "splatoontbds",
    "project-dorado",
    "jerrys-crown-cup",
    "ranchos-royale",
    "splatoon-amateur-circuit",
    # "murfy",
    "sleepy-cafe",
    "rng-bostoffice-remake",
    "coop-wiiu-competitive",
    "dynamic-ink-testing-chamber",
    "bear-industries",
    "splatoonvod-tournaments",
    "dyn",
    "dual-ink",
    "nintendo-online-global",
    "squid-south",
    "shadow-clan-tournaments",
    "cca-collegiate-cephalopod-association",
    "trireme-squid-games",
    "tripnacity",
    "the-reef",
    "inkopolis-bay",
    "little-squid-league",
    "squid-garden",
    "splatcom",
    "midway-ink-tour",
    "turf-be-told",
    "snowpoke",
    "boo-yah-bros",
    "toadstournaments",
    "camos-clan",
    "torchy-gaming",
    "summer-splat-series",
    "xanadu-tournament-series",
    "squidboards-splatoon-2-community-events",
    "young-ink-association",
    "inktv",
    "splatoon-amino-official",
    "regular-gaming-splat2-2",
    "the-ink-squad",
    "under-the-ink",
    "the-owo-gang",
    "splatoon2",
    "deep-sea-solutions",
})


class TournamentLog:
    def __init__(self, file):
        self.file = file

    def add_code(self, code: str):
        with open(self.file, "r") as input_file:
            data = json.load(input_file)

        data.append(code)

        with open(self.file, "w") as output_file:
            json.dump(data, output_file, indent=4)

    def check_code(self, code: str) -> bool:
        with open(self.file, "r") as input_file:
            data = json.load(input_file)
            if code in data:
                return True
            return False


# get the basic info on the tournament
def get_tournament_info(tournament_id: str) -> Optional[dict]:
    r = requests.get(f"https://dtmwra1jsgyb0.cloudfront.net/tournaments/{tournament_id}")
    if r.status_code != 200:
        return None
    return r.json()


def generate_log_json():
    log = TournamentLog("log.json")
    for org in ORG_SLUGS:
        tournaments = battlefyToolkit.tournament_ids(org)
        if tournaments is None:
            continue
        for tournament in tournaments:
            if not log.check_code(tournament):
                tournament_info = get_tournament_info(tournament)
                if tournament_info["gameName"] == "Splatoon 2":
                    log.add_code(tournament)
