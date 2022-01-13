import re
from enum import IntFlag

HE_REGEX = re.compile(r"(^|\W)(he)(\W|$)", re.RegexFlag.MULTILINE | re.RegexFlag.IGNORECASE)
SHE_REGEX = re.compile(r"(^|\W)(she)(\W|$)", re.RegexFlag.MULTILINE | re.RegexFlag.IGNORECASE)
THEY_REGEX = re.compile(r"(^|\W)(they)(\W|$)", re.RegexFlag.MULTILINE | re.RegexFlag.IGNORECASE)
IT_REGEX = re.compile(r"(^|\W)(it)(\W|$)", re.RegexFlag.MULTILINE | re.RegexFlag.IGNORECASE)
NEO_REGEX = re.compile(r"(^|\W)(em|([censvxz])([iey])+r?m?|xyr)s?(elf)?(\W|$)",
                       re.RegexFlag.MULTILINE | re.RegexFlag.IGNORECASE)
ALL_REGEX = re.compile(r"^all$|(^|\W)((pronouns? ?([ :]) ?(all|any))|((all|any) pronouns?))(\W|$)",
                       re.RegexFlag.MULTILINE | re.RegexFlag.IGNORECASE)
ASK_REGEX = re.compile(r"^ask$|(^|\W)((pronouns? ?([ :]) ?(ask))|(ask (for )?pronouns?))(\W|$)",
                       re.RegexFlag.MULTILINE | re.RegexFlag.IGNORECASE)
ANY_REGEX = re.compile(r"(^|\W)(he)(\W|$)", re.RegexFlag.MULTILINE | re.RegexFlag.IGNORECASE)


class PronounFlags(IntFlag):
    """Player's pronoun(s)."""
    NONE = 0
    HE = 1 << 0
    SHE = 1 << 1
    THEY = 1 << 2
    IT = 1 << 3
    NEO = 1 << 4
    ASK = 1 << 5
    ALL = HE | SHE | THEY | IT | NEO | ASK
    ORDER_RTL = 1 << 7
    """If set, the pronoun flags should be read in order right to left, e.g. they/she instead of she/they"""

    @staticmethod
    def from_str(pronouns: str) -> 'PronounFlags':
        # Quick out if serialized byte as string
        if pronouns.isdigit():
            return PronounFlags(pronouns)

        value = PronounFlags.NONE
        if pronouns:
            all_match = ALL_REGEX.search(pronouns)
            if all_match:
                value |= PronounFlags.ALL
            ask_match = ASK_REGEX.search(pronouns)
            if ask_match:
                value |= PronounFlags.ASK
            he_match = HE_REGEX.search(pronouns)
            if he_match:
                value |= PronounFlags.HE
            she_match = SHE_REGEX.search(pronouns)
            if she_match:
                value |= PronounFlags.SHE
                if he_match and he_match.start(1) > she_match.start(1):
                    value |= PronounFlags.ORDER_RTL
            they_match = THEY_REGEX.search(pronouns)
            if they_match:
                value |= PronounFlags.THEY
                if he_match and he_match.start(1) > they_match.start(1):
                    value |= PronounFlags.ORDER_RTL
                if she_match and she_match.start(1) > they_match.start(1):
                    value |= PronounFlags.ORDER_RTL
            it_match = IT_REGEX.search(pronouns)
            if it_match:
                value |= PronounFlags.IT
                if he_match and he_match.start(1) > it_match.start(1):
                    value |= PronounFlags.ORDER_RTL
                if she_match and she_match.start(1) > it_match.start(1):
                    value |= PronounFlags.ORDER_RTL
                if they_match and they_match.start(1) > it_match.start(1):
                    value |= PronounFlags.ORDER_RTL
            neo_match = NEO_REGEX.search(pronouns)
            if neo_match:
                value |= PronounFlags.NEO
                if he_match and he_match.start(1) > neo_match.start(1):
                    value |= PronounFlags.ORDER_RTL
                if she_match and she_match.start(1) > neo_match.start(1):
                    value |= PronounFlags.ORDER_RTL
                if they_match and they_match.start(1) > neo_match.start(1):
                    value |= PronounFlags.ORDER_RTL
                if it_match and it_match.start(1) > neo_match.start(1):
                    value |= PronounFlags.ORDER_RTL
        return value
