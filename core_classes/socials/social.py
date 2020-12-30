from typing import Optional, Union, List
from uuid import UUID

from core_classes.name import Name
from helpers.str_helper import is_none_or_whitespace


class Social(Name):
    social_base_address: str

    def __init__(self,
                 social_base_address: str,
                 value: Optional[str] = None,
                 sources: Union[None, UUID, List[UUID]] = None):
        self.social_base_address = social_base_address
        super().__init__(
            value=self._process_handle(value),
            sources=sources
        )

    def _process_handle(self, new_handle: Optional[str]):
        if is_none_or_whitespace(new_handle):
            return new_handle
        if self.social_base_address in new_handle:
            new_handle = new_handle[new_handle.index(self.social_base_address) + len(self.social_base_address):]
        return new_handle.lstrip("/@ ")

    @property
    def handle(self) -> str:
        return self.value

    @property
    def uri(self) -> str:
        if self.handle is None:
            return self.handle
        else:
            return f'https://{self.social_base_address}/{self.handle}'

    @staticmethod
    def _from_dict(obj: dict, social_base_address: str) -> 'Social':
        assert isinstance(obj, dict)
        name = Name.from_dict(obj)
        return Social(social_base_address, name.value, name.sources)

    def __str__(self):
        return self.uri or self.value or super.__str__(self)
