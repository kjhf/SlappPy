from typing import List

from core_classes.name import Name
from core_classes.socials.battlefy_user_social import BattlefyUserSocial
from helpers.dict_helper import from_list, to_list
from helpers.str_helper import join


class Battlefy:
    slugs: List[BattlefyUserSocial]
    usernames: List[Name]
    persistent_ids: List[Name]

    def __init__(self, slugs=None, usernames=None, persistent_ids=None):
        if slugs is None:
            slugs = []
        if usernames is None:
            usernames = []
        if persistent_ids is None:
            persistent_ids = []
        self.slugs = slugs
        self.usernames = usernames
        self.persistent_ids = persistent_ids

    def __str__(self):
        return f"Slugs: [{join(', ', self.slugs)}], " \
               f"Usernames: [{join(', ', self.usernames)}], " \
               f"Ids: [{join(', ', self.persistent_ids)}]"

    @property
    def battlefy_persistent_id_strings(self) -> List[str]:
        """The known Battlefy Persistent Ids of the Player. Can be Empty."""
        return [social.value for social in self.persistent_ids] \
            if len(self.persistent_ids) > 0 else []

    @staticmethod
    def from_dict(obj: dict) -> 'Battlefy':
        assert isinstance(obj, dict)
        return Battlefy(
            slugs=from_list(lambda x: Name.from_dict(x), obj.get("slugs")),
            usernames=from_list(lambda x: Name.from_dict(x), obj.get("Usernames")),
            persistent_ids=from_list(lambda x: Name.from_dict(x), obj.get("PersistentIds"))
        )

    def to_dict(self) -> dict:
        result = {}
        if len(self.slugs) > 0:
            result["Slugs"] = to_list(lambda x: Name.to_dict(x), self.slugs)
        if len(self.usernames) > 0:
            result["Usernames"] = to_list(lambda x: Name.to_dict(x), self.usernames)
        if len(self.persistent_ids) > 0:
            result["PersistentIds"] = to_list(lambda x: Name.to_dict(x), self.persistent_ids)
        return result
