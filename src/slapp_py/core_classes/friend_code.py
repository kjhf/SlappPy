import hashlib
import logging
import re
from typing import List, Union

import dotenv

from slapp_py.helpers.dict_helper import from_list


class FriendCode:
    fc: List[int] = []

    def __init__(self, param: Union[str, List[int], int]):
        if not param:
            raise ValueError('FriendCode parameter must be specified.')

        elif isinstance(param, str):
            param = [int(part) for part in re.match('^(\\d{4})-(\\d{4})-(\\d{4})$', param).group(1, 2, 3)]

        elif isinstance(param, int):
            string = param.__str__()
            if len(string) < 10 or len(string) > 12:
                raise ValueError(f'The FriendCode in int form should be 9-12 digits long, '
                                 f'actually {len(string)}.')
            param = [
                int(string[-12:-8]),
                int(string[-8:-4]),
                int(string[-4:])
            ]

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
    def from_dict(obj: Union[dict, list]) -> 'FriendCode':
        if isinstance(obj, list):
            return FriendCode(obj)
        elif isinstance(obj, dict):
            # Old form
            return FriendCode(param=from_list(lambda x: int(x), obj.get("FC")))
        else:
            logging.error(f"Unknown FriendCode form: {type(obj)}")
            return NO_FRIEND_CODE

    def to_dict(self) -> list:
        # New form simply returns the short[]
        return self.fc

    def is_3ds_valid_code(self) -> bool:
        fc_int = int(f'{self.fc[0]}{self.fc[1]}{self.fc[2]}')
        principal = fc_int & 0xffffffff
        checksum = fc_int >> 32

        sha1 = hashlib.sha1()
        sha1.update(principal.to_bytes(4, byteorder='little'))
        calc_sum = sha1.digest()[0] >> 1

        logging.info(self.__str__(), fc_int, principal, checksum, calc_sum)
        return checksum == calc_sum


NO_FRIEND_CODE_SHORTS: List[int] = [0, 0, 0]
NO_FRIEND_CODE = FriendCode(NO_FRIEND_CODE_SHORTS)


if __name__ == '__main__':
    dotenv.load_dotenv()
    __entered = input('Enter friend code.')
    try:
        __result = FriendCode(int(__entered))
    except ValueError:
        __result = FriendCode(__entered)

    print(__result)

