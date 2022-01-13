from typing import Optional, Union, List

from slapp_py.core_classes.simple_source import SimpleSource
from slapp_py.core_classes.socials.social import Social

TWITTER_BASE_ADDRESS = "twitter.com"


class Twitter(Social):
    def __init__(self,
                 handle: Optional[str] = None,
                 sources: Union[None, SimpleSource, List[SimpleSource]] = None):
        super().__init__(
            value=handle,
            sources=sources,
            social_base_address=TWITTER_BASE_ADDRESS
        )

    @staticmethod
    def from_dict(obj: dict) -> 'Twitter':
        assert isinstance(obj, dict)
        social = Social._from_dict(obj, TWITTER_BASE_ADDRESS)
        return Twitter(social.handle, social.sources)
