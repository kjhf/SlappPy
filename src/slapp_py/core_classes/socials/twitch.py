from typing import Optional, Union, List

from slapp_py.core_classes.simple_source import SimpleSource
from slapp_py.core_classes.socials.social import Social

TWITCH_BASE_ADDRESS = "twitch.tv"


class Twitch(Social):
    def __init__(self,
                 handle: Optional[str] = None,
                 sources: Union[None, SimpleSource, List[SimpleSource]] = None):
        super().__init__(
            value=handle,
            sources=sources,
            social_base_address=TWITCH_BASE_ADDRESS
        )

    @staticmethod
    def from_dict(obj: dict) -> 'Twitch':
        assert isinstance(obj, dict)
        social = Social._from_dict(obj, TWITCH_BASE_ADDRESS)
        return Twitch(social.handle, social.sources)
