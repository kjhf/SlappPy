import datetime
from typing import Optional, Union, List

from slapp_py.core_classes.simple_source import SimpleSource
from slapp_py.core_classes.socials.social import Social

PLUS_BASE_ADDRESS = "sendou.ink/plus/history/"


class PlusMembership(Social):
    def __init__(self,
                 handle: Optional[str] = None,
                 sources: Union[None, SimpleSource, List[SimpleSource]] = None):
        super().__init__(
            value=handle,
            sources=sources,
            social_base_address=PLUS_BASE_ADDRESS
        )

    @property
    def level(self) -> Optional[int]:
        """Returns the Membership's level as an int (or None)"""
        try:
            return int(self.handle.partition('/')[0])
        except ValueError:
            return None

    @property
    def date(self) -> Optional[datetime.datetime]:
        """Returns the Membership's date"""
        try:
            # in form yyyy/M
            parts = self.handle.split('/')
            return datetime.datetime(year=int(parts[1]), month=int(parts[2]), day=1)
        except ValueError:
            return None

    @staticmethod
    def from_dict(obj: dict) -> 'PlusMembership':
        assert isinstance(obj, dict)
        social = Social._from_dict(obj, PLUS_BASE_ADDRESS)
        return PlusMembership(social.handle, social.sources)

    def __str__(self):
        return f"+{self.level} ({self.date})" if self.level else f"Lost plus membership ({self.date})"
