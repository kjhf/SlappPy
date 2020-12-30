from typing import List

from core_classes.name import Name
from core_classes.socials.battlefy_social import BattlefySocial
from helpers.dict_helper import from_list, to_list
from helpers.str_helper import join


class Battlefy:
    slugs: List[BattlefySocial]
    usernames: List[Name]

    def __init__(self, slugs=None, usernames=None):
        if slugs is None:
            slugs = []
        if usernames is None:
            usernames = []
        self.slugs = slugs
        self.usernames = usernames

    def __str__(self):
        return f"Slugs: [{join(', ', self.slugs)}], Usernames: [{join(', ', self.usernames)}]"

    @staticmethod
    def from_dict(obj: dict) -> 'Battlefy':
        assert isinstance(obj, dict)
        return Battlefy(
            slugs=from_list(lambda x: Name.from_dict(x), obj.get("slugs")),
            usernames=from_list(lambda x: Name.from_dict(x), obj.get("Usernames"))
        )

    def to_dict(self) -> dict:
        result = {}
        if len(self.slugs) > 0:
            result["Slugs"] = to_list(lambda x: Name.to_dict(x), self.slugs)
        if len(self.usernames) > 0:
            result["Usernames"] = to_list(lambda x: Name.to_dict(x), self.usernames)
        return result
