from typing import List

from slapp_py.core_classes.name import Name
from slapp_py.helpers.dict_helper import from_list, to_list
from slapp_py.helpers.str_helper import join


class Discord:
    ids: List[Name]
    usernames: List[Name]

    def __init__(self, ids=None, usernames=None):
        if ids is None:
            ids = []
        if usernames is None:
            usernames = []
        self.ids = ids
        self.usernames = usernames

    def __str__(self):
        return f"Ids: [{join(', ', self.ids)}], Usernames: [{join(', ', self.usernames)}]"

    @staticmethod
    def from_dict(obj: dict) -> 'Discord':
        assert isinstance(obj, dict)
        return Discord(
            ids=from_list(lambda x: Name.from_dict(x), obj.get("Ids")),
            usernames=from_list(lambda x: Name.from_dict(x), obj.get("Usernames"))
        )

    def to_dict(self) -> dict:
        result = {}
        if len(self.ids) > 0:
            result["Ids"] = to_list(lambda x: Name.to_dict(x), self.ids)
        if len(self.usernames) > 0:
            result["Usernames"] = to_list(lambda x: Name.to_dict(x), self.usernames)
        return result
