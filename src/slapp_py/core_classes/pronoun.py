from typing import Union, Optional

from slapp_py.core_classes.pronoun_flags import PronounFlags
from slapp_py.core_classes.simple_source import SimpleSource
from slapp_py.helpers.str_helper import insert

NEO_PLACEHOLDER: str = "(neo)"


class Pronoun:
    value: PronounFlags
    source: SimpleSource

    def __init__(self, value: Union[str, int, PronounFlags] = PronounFlags.NONE, source: Optional[SimpleSource] = None):
        """Construct a Pronoun object."""
        self.value = (value if isinstance(value, PronounFlags)
                      else PronounFlags(value) if isinstance(value, int)
                      else PronounFlags.from_str(value) if isinstance(value, str)
                      else None)
        if not self.value:
            raise TypeError(f"Unknown type passed to Pronoun value: {type(value)}")
        if not source:
            from slapp_py.core_classes.builtins import NO_SOURCE
            self.source = SimpleSource(NO_SOURCE)

    @staticmethod
    def from_dict(obj: dict) -> 'Pronoun':
        if not obj:
            return Pronoun(PronounFlags.NONE)
        else:
            return Pronoun(
                value=obj.get("P"),
                source=SimpleSource.from_serialized(obj.get("S"))
            )

    def to_dict(self) -> dict:
        from slapp_py.core_classes.builtins import NO_SOURCE
        result = {}
        if self.value:
            result["P"] = self.value.value
        if self.source and self.source.__str__() != NO_SOURCE:
            result["S"] = SimpleSource.to_serialized(self.source)
        return result

    def __str__(self):
        """Overridden ToString, returns the pronoun representation in a standard form, e.g. she/her, they/she, etc."""
        switch = {
            PronounFlags.NONE: "none",
            PronounFlags.ALL: "any/all",
            PronounFlags.HE: "he/him",
            PronounFlags.SHE: "she/her",
            PronounFlags.THEY: "they/them",
            PronounFlags.IT: "it/it",
            PronounFlags.NEO: NEO_PLACEHOLDER,
            PronounFlags.ASK: "ask",
        }
        result = switch.get(self.value, None)
        if result:
            return result
        # else we're combining ...
        result = ""
        is_reverse = (self.value & PronounFlags.ORDER_RTL) != 0
        if (self.value & PronounFlags.HE) != 0:
            if is_reverse:
                result = insert(result, 0, "/he")
            else:
                result += "he/"
        if (self.value & PronounFlags.SHE) != 0:
            if is_reverse:
                result = insert(result, 0, "/she")
            else:
                result += "she/"
        if (self.value & PronounFlags.THEY) != 0:
            if is_reverse:
                result = insert(result, 0, "/they")
            else:
                result += "they/"
        if (self.value & PronounFlags.IT) != 0:
            if is_reverse:
                result = insert(result, 0, "/it")
            else:
                result += "it/"
        if (self.value & PronounFlags.NEO) != 0:
            if is_reverse:
                result = insert(result, 0, "/" + NEO_PLACEHOLDER)
            else:
                result += NEO_PLACEHOLDER + "/"
        if (self.value & PronounFlags.ASK) != 0:
            if is_reverse:
                result = insert(result, 0, "/ask")
            else:
                result += "ask/"
        return result.strip(' /')


if __name__ == '__main__':
    test = Pronoun("Discord description + ce/cer or she/her please :)")
    print(test.__str__())
