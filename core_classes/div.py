from typing import Union, Optional

from slapp_py.strings import equals_ignore_case

DIVISION_UNKNOWN_VAL = 2147483647
DIVISION_UNKNOWN_STR = 'Unknown'
DIVISION_X = 0
DIVISION_X_PLUS = -1


class Division:
    def __init__(self,
                 value: Union[int, str, None] = DIVISION_UNKNOWN_VAL,
                 div_type: Optional[str] = DIVISION_UNKNOWN_STR,
                 season: Optional[str] = ""):
        """Constructor for Division"""
        self.value = value if value is not None else DIVISION_UNKNOWN_VAL
        self.div_type = div_type
        self.season = season

        if isinstance(value, str):
            if value == '':
                self.value = DIVISION_UNKNOWN_VAL
            elif value.isnumeric():
                self.value = int(value)
            elif equals_ignore_case(value, 'X+'):
                self.value = DIVISION_X_PLUS
            elif equals_ignore_case(value, 'X'):
                self.value = DIVISION_X
            elif (len(value) > 2) and value[0:3].isnumeric():
                self.value = int(value[0:3])
            elif (len(value) > 1) and value[0:2].isnumeric():
                self.value = int(value[0:2])
            elif value[0:1].isnumeric():
                self.value = int(value[0:1])
            else:
                self.value = DIVISION_UNKNOWN_VAL

    @property
    def name(self) -> str:
        return self.__str__()

    @property
    def normalised_value(self) -> int:
        if self.div_type == 'LUTI':
            return self.value
        elif self.div_type == 'EBTV':
            return self.value + 2
        elif self.div_type == 'DSB':
            return 2 if self.value == 1 \
                else 5 if self.value == 2 \
                else 8
        else:
            return DIVISION_UNKNOWN_VAL

    def __str__(self):
        if self.value is DIVISION_UNKNOWN_VAL:
            return 'Div Unknown'
        else:
            switch = {
                DIVISION_UNKNOWN_VAL: 'Unknown',
                DIVISION_X: 'X',
                DIVISION_X_PLUS: 'X+',
            }
            value_str = switch.get(self.value, str(self.value))
            return f'{self.div_type} {self.season} Div {value_str}'

    def __cmp__(self, other):
        if isinstance(other, Division):
            return self.normalised_value.__cmp__(other.normalised_value)
        else:
            raise TypeError(f'Cannot compare a Division to a non-Division type: {other}')

    def __lt__(self, other):
        return self.__cmp__(other) == -1
