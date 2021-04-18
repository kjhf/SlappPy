import random

from slapp_py import weapons


def get_random_footer_phrase() -> str:
    return random\
        .choice(FOOTER_PHRASES)\
        .replace('%weapon%', weapons.get_random_weapon())


FOOTER_PHRASES = [
    "SPLATOON 3! ",
    "You should Step Up, Europe. ",
    "Play LowInk. ",
    "Thank your TOs. ",
    "This sentence was written past 3am. ",
    "Slate loves Wug. ",
    "Has anyone told you that you're awesome? 🥰 ",
    "Orange is the new black. ",
    "Imagine a computer program to be non-binary. Haha. ",
    "Trans rights! ",
    "Just ignore when I used to tell you how long a query took. I lied about it. ",
    "You can join the dev server at https://discord.gg/wZZv2Cr",
    "I'm written in Python, Slapp is written in C#, but Slate is written in cups of tea and base 4 GCAT. ",
    "Just ignore when I used to tell you how long a query took. I lied about it. ",
    "Don't shoot the messenger. ",
    "Slate says hi. ",
    "Stonks. ",
    "http://aws.random.cat 🐱 ",
    "https://random.dog/ 🐕 ",
    "#SaveMelee ",
    "Be kind to one another. ",
    "Peace was never an option. 🔪 ",
    "Keep it up! You're doing great! ",
    "Coffee time? ",
    "Please don't enter entire song lyrics as your name. ",
    "Did you know that I have a ~jpg function? ",
    "A Minnow is a small freshwater fish and also a tourney that you should join. ",
    "I'm just here to make your verification experience slightly easier. Running the tournament? Nah, not my thing. ",
    "The real journey was the friends we made along the way. ",
    "Are you looking after yourself? ",
    "Stay hydrated, human. I'll pass on it though. ",
    "Other... games...? ",
    "BINGO! ",
    "The answer is... yes, that one. ",
    "The answer is... no. ",
    "Let's go to the Winchester, have a nice cold pint, and wait for this all to blow over. ",
    "SSWWAAAAAANN 🦢 ",
    "Check out 'is 'arse 🐴 ",
    "*Sweats nervously* ",
    "Did you take the red pill or the blue pill? ",
    "*You hear Megalovania playing off in the distance* ",
    "Do you remember when Nintendo released the SOS 2020 poster? Good times. ",
    "Sus. ",
    "We BOUNCE THAT BOI ",
    "I do not say poggies. ",
    "Doing it for the fans! Fans love it! ",
    "I'll have two number 9s, a number 6 with extra dip, a number 7, two number 45s, one with cheese, and a large soda. ",
    "Thanks Inkipedia! ",
    "42. ",
    "Ceci n'est pas une pipe. ",
    "Your weapon of the day is... %weapon%! ",
    "The spirits tell me... %weapon%! ",
    "We're only human after all. ",
    "Do not be sad because they left, be happy because they existed. ",
    "Buy it, use it, break it, fix it, trash it, change it, mail, upgrade it... ",
    "Soon may the Wellerman come, to bring us sugar and tea and rum... ",
    "What is love? ",
    "You will be baked. And then there will be cake. ",
    "The square root of rope is string. ",
    "At some point in their lives 1 in 6 children will be abducted by the Dutch. ",
    "Humans can survive underwater. But not for very long. "
]
