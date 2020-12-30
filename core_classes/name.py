from typing import List, Optional, Union
from uuid import UUID


class Name:
    value: str
    sources: List[UUID]

    def __init__(self,
                 value: Optional[str] = None,
                 sources: Union[None, UUID, List[UUID]] = None):
        if value is None:
            value = ""

        if not sources:
            from core_classes.builtins import BuiltinSource
            self.sources = [BuiltinSource.guid]
        else:
            if not isinstance(sources, list):
                sources = [sources]

            self.sources = []
            for i in range(0, len(sources)):
                assert isinstance(sources[i], UUID)
                self.sources.append(sources[i])

        self.value = value

    @staticmethod
    def from_dict(obj: dict) -> 'Name':  # Python note: 'Name' in '' to forward-declare the type as we're in the class.
        assert isinstance(obj, dict)
        from core_classes.source import Source
        return Name(
            value=obj.get("Value", ""),
            sources=Source.deserialize_uuids(obj)
        )

    def to_dict(self) -> dict:
        result: dict = {'Value': self.value}
        if len(self.sources) > 0:
            result["S"] = map(str, self.sources)
        return result

    def __str__(self):
        return self.value
