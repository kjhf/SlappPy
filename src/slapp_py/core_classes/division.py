from typing import Union, Optional, Tuple

from slapp_py.helpers.str_helper import equals_ignore_case

DIVISION_UNKNOWN_VAL = 2147483647
DIV_TYPE_UNKNOWN_STR = 'Unknown'
DIVISION_UNKNOWN_STR = 'Div Unknown'
SEASON_UNKNOWN_STR = ''
_VALUE_SEPARATOR_STR = " Div "
DIVISION_X = 0
DIVISION_X_PLUS = -1


class Division:
    value: int
    div_type: str
    season: str

    def __init__(self,
                 value_or_serialized: Union[int, str, None] = None,
                 div_type: Optional[str] = None,
                 season: Optional[str] = None):
        """Constructor for Division"""

        if isinstance(value_or_serialized, str):
            if value_or_serialized == '':
                self.value = DIVISION_UNKNOWN_VAL
            elif div_type is None and not season:
                # If the other args were not specified, parse the division as a str only.
                (self.value, self.div_type, self.season) = Division.from_str(value_or_serialized)
                return
            else:
                # Other values are specified. Parse the value only.
                self.value = Division.parse_value_str(value_or_serialized)
        elif isinstance(value_or_serialized, int):
            self.value = value_or_serialized
        else:
            self.value = DIVISION_UNKNOWN_VAL

        self.div_type = div_type or DIV_TYPE_UNKNOWN_STR
        self.season = season or SEASON_UNKNOWN_STR

    @property
    def name(self) -> str:
        return self.__str__()

    @property
    def is_unknown(self) -> bool:
        return self.value == DIVISION_UNKNOWN_VAL or \
               self.div_type == DIV_TYPE_UNKNOWN_STR

    @property
    def normalised_value(self) -> int:
        if self.div_type == 'LUTI':
            return self.value if self.value != DIVISION_X_PLUS else DIVISION_X  # From S11, group X and X+ together.
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
            return DIVISION_UNKNOWN_STR
        else:
            switch = {
                DIVISION_UNKNOWN_VAL: DIV_TYPE_UNKNOWN_STR,
                DIVISION_X: 'X',
                DIVISION_X_PLUS: 'X+',
            }
            value_str = switch.get(self.value, str(self.value))
            return f'{self.div_type} {self.season}{_VALUE_SEPARATOR_STR}{value_str}'

    def __cmp__(self, other):
        if isinstance(other, Division):
            x = self.normalised_value
            y = other.normalised_value
            return (x > y) - (x < y)
        else:
            raise TypeError(f'Cannot compare a Division to a non-Division type: {other}')

    def __lt__(self, other):
        """Remember, lower div is better."""
        return self.__cmp__(other) == -1

    def __eq__(self, other):
        if isinstance(other, Division):
            return (self.value == other.value
                    and self.div_type == other.div_type
                    and self.season == other.season)
        else:
            return False

    def __hash__(self):
        return hash(f'{self.div_type}{self.season}{self.value}')

    @staticmethod
    def parse_value_str(incoming: str):
        """Translates the value string into a suitable integer. DIVISION_UNKNOWN_VAL if unknown."""
        if not incoming:
            return DIVISION_UNKNOWN_VAL
        # else
        incoming = incoming.strip()
        if incoming.isnumeric():
            value = int(incoming)
        elif equals_ignore_case(incoming, 'X+'):
            value = DIVISION_X_PLUS
        elif equals_ignore_case(incoming, 'X'):
            value = DIVISION_X
        elif (len(incoming) > 3) and incoming[0:4].isnumeric():
            value = int(incoming[0:3])
        elif (len(incoming) > 2) and incoming[0:3].isnumeric():
            value = int(incoming[0:3])
        elif (len(incoming) > 1) and incoming[0:2].isnumeric():
            value = int(incoming[0:2])
        elif incoming[0:1].isnumeric():
            value = int(incoming[0:1])
        else:
            value = DIVISION_UNKNOWN_VAL
        return value

    @staticmethod
    def from_dict(obj: dict) -> 'Division':
        assert isinstance(obj, dict)
        value = obj.get("Value", DIVISION_UNKNOWN_VAL)
        if isinstance(value, str):
            value = int(value)
        div_type = obj.get("DivType", DIV_TYPE_UNKNOWN_STR)
        season = obj.get("Season", SEASON_UNKNOWN_STR).strip()
        return Division(value, div_type, season)

    @staticmethod
    def from_str(serialized: str) -> Tuple[int, str, str]:
        """Parse the division from its string rep, returning the int value, div type, and season."""
        if serialized == DIVISION_UNKNOWN_STR:
            return DIVISION_UNKNOWN_VAL, DIV_TYPE_UNKNOWN_STR, SEASON_UNKNOWN_STR
        else:
            index = serialized.find(" ")
            if index < 0:
                return DIVISION_UNKNOWN_VAL, DIV_TYPE_UNKNOWN_STR, SEASON_UNKNOWN_STR
            else:
                div_type_str = serialized[:index]
                serialized = serialized[index + 1:]
                index = serialized.find(_VALUE_SEPARATOR_STR)
                if index < 0:
                    return DIVISION_UNKNOWN_VAL, DIV_TYPE_UNKNOWN_STR, SEASON_UNKNOWN_STR
                else:
                    season = serialized[:index].strip()
                    value = Division.parse_value_str(serialized[index + len(_VALUE_SEPARATOR_STR):])
                    return value, div_type_str, season

    def to_dict(self) -> dict:
        result: dict = {"Value": self.value, "DivType": self.div_type, "Season": self.season}
        return result

    def to_serialized(self):
        return self.__str__()


Unknown = Division()
