import logging
from typing import List, Union, Dict, Optional

from slapp_py.core_classes.friend_code import FriendCode
from slapp_py.core_classes.simple_source import SimpleSource
from slapp_py.helpers.dict_helper import first_key, order_dict_by_value


class FriendCodeHandler:
    _codes: Dict[FriendCode, List[SimpleSource]]
    _ordered: bool = False

    def __init__(self, codes: Optional[Dict[FriendCode, List[SimpleSource]]] = None):
        self._codes = codes or {}

    @property
    def count(self):
        return len(self._codes)

    @property
    def current_code(self):
        """Get the latest friend code in this information, or None."""
        if not self._ordered:
            self._order_codes()
        return first_key(self._codes, None)

    def add(self, incoming: Union[FriendCode, List[FriendCode]], sources: Union[SimpleSource, List[SimpleSource]]):
        if not incoming or not sources:
            return
        if not isinstance(incoming, list):
            incoming = [incoming]

        self._ordered = False
        for to_add in incoming:
            if to_add.no_code:
                continue
            self._codes.setdefault(to_add, []).extend(SimpleSource.from_serialized(sources))

    def merge(self, handler: 'FriendCodeHandler'):
        for key, value in handler._codes.items():
            self.add(key, value)

    def filter_to_source(self, source_id: SimpleSource) -> 'FriendCodeHandler':
        return FriendCodeHandler(
            codes={k: v for k, v in self._codes.items() if source_id in v}
        )

    def get_sources_for_code(self, fc: FriendCode) -> List[SimpleSource]:
        """Gets sources for the code, or empty if not found."""
        return self._codes.get(fc, [])

    def get_sources_flat(self) -> List[SimpleSource]:
        """Gets sources contained in this information."""
        return list(set([result for sublist in self._codes.values() for result in sublist]))

    def get_codes_unordered(self):
        """Get the codes without the sources."""
        return list(self._codes.keys())

    def get_codes_ordered(self):
        """Get the codes without the sources in chronological order from most recent."""
        if not self._ordered:
            self._order_codes()
        return self.get_codes_unordered()

    def get_codes_sourced(self) -> Dict[FriendCode, List[SimpleSource]]:
        """Get the codes with sources."""
        return {k: v for k, v in self._codes.items()}

    def _order_codes(self):
        self._codes = order_dict_by_value(self._codes, reverse=True)
        self._ordered = True

    @staticmethod
    def from_dict(obj: dict) -> 'FriendCodeHandler':
        assert isinstance(obj, dict)
        try:
            val_dict = obj.get("C")
            result = FriendCodeHandler()
            for key, value in val_dict.items():
                result.add(FriendCode(key), SimpleSource.from_serialized(value))
            return result
        except Exception as e:
            logging.exception(exc_info=e, msg=f"Exception occurred loading Friend Code Handler: {e}, {e.args}")
            raise e

    def to_dict(self) -> dict:
        result = {}
        if len(self._codes) > 0:
            result["C"] = {k.to_int(): SimpleSource.to_serialized(v) for k, v in self._codes.items()}
        return result

    def __str__(self):
        return f"{self.count} FCs{(f', {first_key(self._codes)}' if self.count > 0 else '')}"
