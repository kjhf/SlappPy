import random
from typing import Optional

WEAPONS = [
    ".52 Gal",
    ".52 Gal Deco",
    ".96 Gal",
    ".96 Gal Deco",
    "Aerospray MG",
    "Aerospray PG",
    "Aerospray RG",
    "Ballpoint Splatling",
    "Ballpoint Splatling Nouveau",
    "Bamboozler 14 Mk I",
    "Bamboozler 14 Mk II",
    "Bamboozler 14 Mk III",
    "Blaster",
    "Bloblobber",
    "Bloblobber Deco",
    "Carbon Roller",
    "Carbon Roller Deco",
    "Cherry H-3 Nozzlenose",
    "Clash Blaster",
    "Clash Blaster Neo",
    "Classic Squiffer",
    "Clear Dapple Dualies",
    "Custom Blaster",
    "Custom Dualie Squelchers",
    "Custom E-Liter 4K",
    "Custom E-Liter 4K Scope",
    "Custom Explosher",
    "Custom Goo Tuber",
    "Custom Hydra Splatling",
    "Custom Jet Squelcher",
    "Custom Range Blaster",
    "Custom Splattershot Jr.",
    "Dapple Dualies",
    "Dapple Dualies Nouveau",
    "Dark Tetra Dualies",
    "Dualie Squelchers",
    "Dynamo Roller",
    "E-Liter 4K",
    "E-Liter 4K Scope",
    "Enberry Splat Dualies",
    "Explosher",
    "Firefin Splat Charger",
    "Firefin Splatterscope",
    "Flingza Roller",
    "Foil Flingza Roller",
    "Foil Squeezer",
    "Forge Splattershot Pro",
    "Fresh Squiffer",
    "Glooga Dualies",
    "Glooga Dualies Deco",
    "Gold Dynamo Roller",
    "Goo Tuber",
    "Grim Range Blaster",
    "H-3 Nozzlenose",
    "H-3 Nozzlenose D",
    "Heavy Splatling",
    "Heavy Splatling Deco",
    "Heavy Splatling Remix",
    "Hero Blaster Replica",
    "Hero Brella Replica",
    "Hero Charger Replica",
    "Hero Dualie Replicas",
    "Hero Roller Replica",
    "Hero Shot Replica",
    "Hero Slosher Replica",
    "Hero Splatling Replica",
    "Herobrush Replica",
    "Hydra Splatling",
    "Inkbrush",
    "Inkbrush Nouveau",
    "Jet Squelcher",
    "Kensa .52 Gal",
    "Kensa Charger",
    "Kensa Dynamo Roller",
    "Kensa Glooga Dualies",
    "Kensa L-3 Nozzlenose",
    "Kensa Luna Blaster",
    "Kensa Mini Splatling",
    "Kensa Octobrush",
    "Kensa Rapid Blaster",
    "Kensa Sloshing Machine",
    "Kensa Splat Dualies",
    "Kensa Splat Roller",
    "Kensa Splatterscope",
    "Kensa Splattershot",
    "Kensa Splattershot Jr.",
    "Kensa Splattershot Pro",
    "Kensa Undercover Brella",
    "Krak-On Splat Roller",
    "L-3 Nozzlenose",
    "L-3 Nozzlenose D",
    "Light Tetra Dualies",
    "Luna Blaster",
    "Luna Blaster Neo",
    "Mini Splatling",
    "N-Zap '83",
    "N-Zap '85",
    "N-Zap '89",
    "Nautilus 47",
    "Nautilus 79",
    "Neo Splash-o-matic",
    "Neo Sploosh-o-matic",
    "New Squiffer",
    "Octobrush",
    "Octobrush Nouveau",
    "Octo Shot Replica",
    "Permanent Inkbrush",
    "Range Blaster",
    "Rapid Blaster", "Ink Mine",
    "Rapid Blaster Deco",
    "Rapid Blaster Pro",
    "Rapid Blaster Pro Deco",
    "Slosher",
    "Slosher Deco",
    "Sloshing Machine",
    "Sloshing Machine Neo",
    "Soda Slosher",
    "Sorella Brella",
    "Splash-o-matic",
    "Splat Brella",
    "Splat Charger",
    "Splat Dualies",
    "Splat Roller",
    "Splatterscope",
    "Splattershot",
    "Splattershot Jr.",
    "Splattershot Pro",
    "Sploosh-o-matic",
    "Sploosh-o-matic 7",
    "Squeezer",
    "Tenta Brella",
    "Tenta Camo Brella",
    "Tenta Sorella Brella",
    "Tentatek Splattershot",
    "Tri-Slosher",
    "Tri-Slosher Nouveau",
    "Undercover Brella",
    "Undercover Sorella Brella",
    "Zink Mini Splatling"
]


def transform_weapon(wep: str) -> str:
    wep = wep.lower()
    wep = wep.rstrip(" s")  # In case of "dualies" or tetras"
    wep = wep.replace("splat ", "")
    wep = wep.replace("classic ", "")
    wep = wep.replace("replica ", "")
    wep = wep.replace("kensa ", "k")
    wep = wep.replace("custom ", "c")
    wep = wep.replace("deco ", "d")
    wep = wep.replace("nouveau ", "n")
    wep = wep.replace("zink ", "z")
    wep = wep.replace("-", "")
    wep = wep.replace(".", "")
    wep = wep.replace("'", "")
    wep = wep.replace(" ", "")

    # Special changes
    wep = wep.replace("duel", "dual")
    wep = wep.replace("nautilus", "naut")
    wep = wep.replace("omatic", "")
    wep = wep.replace("squelcher", "")
    wep = wep.replace("squiffer", "squiff")
    wep = wep.replace("nozzlenose", "")  # The Nozzles are usually known by their names
    wep = wep.replace("splatling", "")  # The Splatlings are usually known by their names
    wep = wep.replace("heavyremix", "remix")
    wep = wep.replace("14mk", "")  # These are common to bamboos so boring
    wep = wep.replace("tuber", "")  # These are common to goo tuber so boring
    wep = wep.replace("splattershotpro", "pro")  # Known as pros
    wep = wep.replace("splattershot", "shot")  # Known as shots
    wep = wep.replace("splatterscope", "scope")  # Known as scopes
    wep = wep.replace("sloshingmachine", "machine")  # Known as machines
    wep = wep.replace("bloblobber", "blob")  # Known as blobs
    wep = wep.replace("explosher", "explo")  # Usually shortened
    wep = wep.replace("explosh", "explo")  # Usually shortened
    wep = wep.replace("tenta", "tent")  # Usually shortened
    wep = wep.replace("sodaslosher", "soda")  # Blasters are known by their names, ...
    wep = wep.replace("rapidblaster", "rapid")  # but we can't remove blaster because that's a weapon
    wep = wep.replace("lunablaster", "luna")
    wep = wep.replace("rangeblaster", "range")
    wep = wep.replace("dynamoroller", "dynamo")  # Rollers are known by their names, ...
    wep = wep.replace("carbonroller", "carbon")  # but we can't remove roller because that's the splat weapon
    wep = wep.replace("flingzaroller", "fling")
    wep = wep.replace("flingroller", "fling")
    wep = wep.replace("flingza", "fling")
    wep = wep.replace("tetras", "tetra")  # tetras should be tetra dualies
    return wep


TRANSFORMED_WEAPONS = list(map(lambda w: transform_weapon(w), WEAPONS))


def get_random_weapon() -> str:
    return random.choice(WEAPONS)


def try_find_weapon(search: str, exact: bool = False) -> Optional[str]:
    result = next((w for w in WEAPONS if w == search), None)
    if result or exact:
        return result
    else:
        # Search inexact
        search = search.lower()

        # Special exceptions
        if search == "clappies":
            return "Clear Dapple Dualies"
        elif search == "zimi":
            return "Zink Mini Splatling"
        elif search == "kimi":
            return "Kensa Mini Splatling"
        elif search == "kunder":
            return "Kensa Undercover Brella"
        elif search == "tetras":
            return "Dark Tetra Dualies"
        else:
            for i, t in enumerate(TRANSFORMED_WEAPONS):
                if t == transform_weapon(search):
                    return WEAPONS[i]

        return None
