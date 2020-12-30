from typing import List

from helpers.dict_helper import from_list


class FriendCode:
    fc: List[int] = []

    def __init__(self, param: List[int]):
        if not param or len(param) != 3:
            raise ValueError('param should be length 3.')
        self.fc = param

    # TODO - parse FCs from string (this is implemented in C#)
    # @staticmethod
    # def parse_and_strip_fc(value: str) -> ('FriendCode', str):
    #     if is_none_or_whitespace(value):
    #         return NO_FRIEND_CODE, value
    #
    # @staticmethod
    # def try_parse(value: str) -> (bool, 'FriendCode'):
    #     (fc, _) = FriendCode.parse_and_strip_fc(value)
    #     return fc != NO_FRIEND_CODE, fc

    def __str__(self, separator: str = '-'):
        if not self.fc:
            return "(not set)"

        return f'{self.fc[0]:04}{separator}{self.fc[1]:04}{separator}{self.fc[2]:04}'

    def __eq__(self, other):
        if not isinstance(other, FriendCode):
            return False
        if len(self.fc) == len(other.fc):
            return all(self.fc[i] == other.fc[i] for i in range(0, 3))
        else:
            return False

    @staticmethod
    def from_dict(obj: dict) -> 'FriendCode':
        assert isinstance(obj, dict)
        return FriendCode(param=from_list(lambda x: int(x), obj.get("FC")))

    def to_dict(self) -> dict:
        result: dict = {"FC": self.fc}
        return result


NO_FRIEND_CODE_SHORTS: List[int] = [0, 0, 0]
NO_FRIEND_CODE = FriendCode(NO_FRIEND_CODE_SHORTS)
