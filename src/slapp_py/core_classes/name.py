from typing import List, Optional, Union
from slapp_py.core_classes.simple_source import SimpleSource


class Name:
    value: str
    sources: List[SimpleSource]

    def __init__(self,
                 value: Optional[str] = None,
                 sources: Union[None, SimpleSource, List[SimpleSource]] = None):
        if value is None:
            value = ""

        # This handles the str/list/SimpleSource combinations
        sources: Optional[List[SimpleSource]] = SimpleSource.from_serialized(sources)
        if not sources:
            from slapp_py.core_classes.builtins import NO_SOURCE
            self.sources = [SimpleSource(NO_SOURCE)]
        else:
            self.sources = sources

        self.value = value

    @staticmethod
    def from_dict(obj: dict) -> 'Name':
        assert isinstance(obj, dict)
        return Name(
            value=obj.get("N", ""),
            sources=SimpleSource.from_serialized(obj.get("S", None))
        )

    def to_dict(self) -> dict:
        result: dict = {'N': self.value}
        if len(self.sources) > 0:
            result["S"] = SimpleSource.to_serialized(self.sources)
        return result

    def __str__(self):
        return self.value
