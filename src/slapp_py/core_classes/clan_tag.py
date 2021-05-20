from typing import Optional, List
from uuid import UUID

from slapp_py.core_classes.name import Name
from slapp_py.core_classes.tag_option import TagOption


class ClanTag(Name):
    layout_option: Optional[TagOption]

    def __init__(self, value: Optional[str],
                 sources: Optional[List[UUID]] = None,
                 layout_option: Optional[TagOption] = TagOption.Unknown) -> None:
        if sources is None:
            sources = []

        super().__init__(value, sources)

        self.layout_option = layout_option

    @staticmethod
    def from_dict(obj: dict) -> 'ClanTag':
        assert isinstance(obj, dict)
        name = Name.from_dict(obj)

        layout_option: str = obj.get("LayoutOption", TagOption.Unknown)
        if isinstance(layout_option, str):
            layout_option = TagOption[layout_option]
        assert isinstance(layout_option, TagOption)
        return ClanTag(name.value, name.sources, layout_option)

    def to_dict(self) -> dict:
        result = Name.to_dict(self)
        result["LayoutOption"] = self.layout_option.name
        return result
