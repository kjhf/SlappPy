from typing import Optional, Union, List
from slapp_py.core_classes.simple_source import SimpleSource
from slapp_py.core_classes.socials.social import Social

SENDOU_BASE_ADDRESS = "sendou.ink/u"


class Sendou(Social):
    def __init__(self,
                 handle: Optional[str] = None,
                 sources: Union[None, SimpleSource, List[SimpleSource]] = None):
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
