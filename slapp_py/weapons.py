import random

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


def get_random_weapon() -> str:
    return random.choice(WEAPONS)
