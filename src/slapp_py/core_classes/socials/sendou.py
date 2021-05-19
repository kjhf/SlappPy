from typing import Optional, Union, List
from uuid import UUID

from slapp_py.core_classes.socials.social import Social

SENDOU_BASE_ADDRESS = "sendou.ink/u"


class Sendou(Social):
    def __init__(self,
                 handle: Optional[str] = None,
                 sources: Union[None, UUID, List[UUID]] = None):
        super().__init__(
            value=handle,
            sources=sources,
            social_base_address=SENDOU_BASE_ADDRESS
        )

    @staticmethod
    def from_dict(obj: dict) -> 'Sendou':
        assert isinstance(obj, dict)
        social = Social._from_dict(obj, SENDOU_BASE_ADDRESS)
        return Sendou(social.handle, social.sources)
