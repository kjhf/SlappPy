import hashlib
import logging
import re
from typing import List, Union
from slapp_py.helpers.dict_helper import from_list


class FriendCode:
    fc_short_1: int
    fc_short_2: int
    fc_short_3: int

    def __init__(self, param: Union[str, List[int], int]):
        if not param:
            raise ValueError('FriendCode parameter must be specified.')

        if isinstance(param, int):
            param = param.__str__()

        if isinstance(param, str):
            if param.isnumeric():
                if len(param) < 9 or len(param) > 12:
                    raise ValueError(f'The FriendCode in int form should be 9-12 digits long, '
                                     f'actually {len(param)}.')
                param = [
                    int(param[-12:-8]),
                    int(param[-8:-4]),
                    int(param[-4:])
                ]
            else:
                try:
                    param = [int(part) for part in re.search(r"\(?(SW|FC|sw|fc)?\s*([:\-=])?\s?(\d{4})\s*([- ._/=])\s*(\d{4})\s*([- ._/=])\s*(\d{4})\s*\)?", param).group(3, 5, 7)]
                except AttributeError:
                    raise ValueError("Can't parse the specified Friend Code: " + param)

        if len(param) != 3:
            raise ValueError('FriendCode should be 3 ints.')

        self.fc_short_1 = param[0]
        self.fc_short_2 = param[1]
        self.fc_short_3 = param[2]

    @property
    def no_code(self) -> bool:
        return self.fc_short_1 == 0 and self.fc_short_2 == 0 and self.fc_short_3 == 0

    def __str__(self, separator: str = '-'):
        if self.no_code:
            return "(not set)"

        return f'{self.fc_short_1:04}{separator}{self.fc_short_2:04}{separator}{self.fc_short_3:04}'

    def __hash__(self) -> int:
        return self.to_int()

    def __eq__(self, other):
        if not isinstance(other, FriendCode):
            return False

        return (self.fc_short_1 == other.fc_short_1
                and self.fc_short_2 == other.fc_short_2
                and self.fc_short_3 == other.fc_short_3)

    @staticmethod
    def from_serialized(obj: Union[dict, list, str]) -> 'FriendCode':
        if isinstance(obj, list) or isinstance(obj, str):
            return FriendCode(obj)
        elif isinstance(obj, dict):
            # Old form
            return FriendCode(param=from_list(lambda x: int(x), obj.get("FC")))
        else:
            logging.error(f"Unknown FriendCode form: {type(obj)}")
            return FriendCode([0, 0, 0])

    def to_dict(self) -> list:
        # New form simply returns the short[]
        return [self.fc_short_1, self.fc_short_2, self.fc_short_3]

    def to_int(self):
        return 0 if self.no_code else int(self.__str__(''))

    def is_3ds_valid_code(self) -> bool:
        fc_int = self.to_int()
        principal = fc_int & 0xffffffff
        checksum = fc_int >> 32

        sha1 = hashlib.sha1()
        sha1.update(principal.to_bytes(4, byteorder='little'))
        calc_sum = sha1.digest()[0] >> 1

        logging.info(self.__str__(), fc_int, principal, checksum, calc_sum)
        return checksum == calc_sum


if __name__ == '__main__':
    import dotenv
    dotenv.load_dotenv()
    __entered = input('Enter friend code.')
    try:
        __result = FriendCode(int(__entered))
    except ValueError:
        __result = FriendCode(__entered)

    print(__result)
