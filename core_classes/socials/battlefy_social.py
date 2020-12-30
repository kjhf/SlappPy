from typing import Optional, Union, List
from uuid import UUID

from core_classes.socials.social import Social

BATTLEFY_BASE_ADDRESS = "battlefy.com/users"


class BattlefySocial(Social):
    def __init__(self,
                 handle: Optional[str] = None,
                 sources: Union[None, UUID, List[UUID]] = None):
        super().__init__(
            value=handle,
            sources=sources,
            social_base_address=BATTLEFY_BASE_ADDRESS
        )

    @staticmethod
    def from_dict(obj: dict) -> 'BattlefySocial':
        assert isinstance(obj, dict)
        social = Social._from_dict(obj, BATTLEFY_BASE_ADDRESS)
        return BattlefySocial(social.handle, social.sources)
