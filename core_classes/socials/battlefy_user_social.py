from typing import Optional, Union, List
from uuid import UUID

from core_classes.socials.social import Social

BATTLEFY_BASE_ADDRESS = "battlefy.com/users"


class BattlefyUserSocial(Social):
    def __init__(self,
                 battlefy_slug: Optional[str] = None,
                 sources: Union[None, UUID, List[UUID]] = None):
        super().__init__(
            value=battlefy_slug,
            sources=sources,
            social_base_address=BATTLEFY_BASE_ADDRESS
        )

    @staticmethod
    def from_dict(obj: dict) -> 'BattlefyUserSocial':
        assert isinstance(obj, dict)
        social = Social._from_dict(obj, BATTLEFY_BASE_ADDRESS)
        return BattlefyUserSocial(social.handle, social.sources)
