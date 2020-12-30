from typing import Union, Optional

from helpers.str_helper import equals_ignore_case

DIVISION_UNKNOWN_VAL = 2147483647
DIVISION_UNKNOWN_STR = 'Unknown'
DIVISION_X = 0
DIVISION_X_PLUS = -1


class Division:
    value: int
    div_type: str
    season: str

    def __init__(self,
                 value: Union[int, str, None] = DIVISION_UNKNOWN_VAL,
                 div_type: Optional[str] = DIVISION_UNKNOWN_STR,
                 season: Optional[str] = ""):
        """Constructor for Division"""
        self.div_type = div_type or DIVISION_UNKNOWN_STR
        self.season = season or ""

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
        elif isinstance(value, int):
            self.value = value
        else:
            self.value = DIVISION_UNKNOWN_VAL

    @property
    def name(self) -> str:
        return self.__str__()

    @property
    def is_unknown(self) -> bool:
        return self.value == DIVISION_UNKNOWN_VAL or \
               self.div_type == DIVISION_UNKNOWN_STR

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

    @staticmethod
    def from_dict(obj: dict) -> 'Division':
        assert isinstance(obj, dict)
        value = obj.get("Value", DIVISION_UNKNOWN_VAL)
        if isinstance(value, str):
            value = int(value)
        div_type = obj.get("DivType", DIVISION_UNKNOWN_STR)
        season = obj.get("Season", '')
        return Division(value, div_type, season)

    def to_dict(self) -> dict:
        result: dict = {"Value": self.value, "DivType": self.div_type, "Season": self.season}
        return result


Unknown = Division()
