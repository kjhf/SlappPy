import hashlib
import re
from typing import List, Union

from helpers.dict_helper import from_list


class FriendCode:
    fc: List[int] = []

    def __init__(self, param: Union[str, List[int]]):
        if not param:
            raise ValueError('FriendCode parameter must be specified.')

        if isinstance(param, str):
            param = [int(part) for part in re.match('^(\\d{4})-(\\d{4})-(\\d{4})$', param).group(1, 2, 3)]

        if len(param) != 3:
            raise ValueError('FriendCode should be 3 ints.')

        self.fc = param

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

    def is_3ds_valid_code(self) -> bool:
        fc_int = int(f'{self.fc[0]}{self.fc[1]}{self.fc[2]}')
        principal = fc_int & 0xffffffff
        checksum = fc_int >> 32

        sha1 = hashlib.sha1()
        sha1.update(principal.to_bytes(4, byteorder='little'))
        calc_sum = sha1.digest()[0] >> 1

        print(self.__str__(), fc_int, principal, checksum, calc_sum)
        return checksum == calc_sum


NO_FRIEND_CODE_SHORTS: List[int] = [0, 0, 0]
NO_FRIEND_CODE = FriendCode(NO_FRIEND_CODE_SHORTS)


if __name__ == '__main__':
    fc = FriendCode(input('Enter friend code.'))
    print(fc)
