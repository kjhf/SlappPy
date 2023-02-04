import logging
from typing import List, Union, Dict, Optional

from slapp_py.core_classes.division import Division
from slapp_py.core_classes.simple_source import SimpleSource
from slapp_py.helpers.dict_helper import first_key, order_dict_by_value


class DivisionsHandler:
    _divs: Dict[Division, List[SimpleSource]]
    _ordered: bool = False

    def __init__(self, divs: Optional[Dict[Division, List[SimpleSource]]] = None):
        self._divs = divs or {}

    @property
    def count(self):
        return len(self._divs)

    @property
    def current_div(self):
        """Get the current div in the Divisions in this information."""
        from slapp_py.core_classes import division
        if not self._ordered:
            self._order_divs()
        return first_key(self._divs, division.Unknown)

    def add(self, incoming: Union[Division, List[Division]], sources: Union[SimpleSource, List[SimpleSource]]):
        if not incoming or not sources:
            return
        if not isinstance(incoming, list):
            incoming = [incoming]

        self._ordered = False
        for to_add in incoming:
            if to_add.is_unknown:
                continue
            self._divs.setdefault(to_add, []).extend(SimpleSource.from_serialized(sources))

    def filter_to_source(self, source_id: SimpleSource) -> 'DivisionsHandler':
        return DivisionsHandler(
            divs={k: v for k, v in self._divs.items() if source_id in v}
        )

    def get_sources_for_division(self, div: Division) -> List[SimpleSource]:
        """Gets sources for the division, or empty if not found."""
        return self._divs.get(div, [])

    def get_sources_flat(self) -> List[SimpleSource]:
        """Gets sources contained in this information."""
        return list(set([result for sublist in self._divs.values() for result in sublist]))

    def get_divs_unordered(self):
        """Get the divisions without the sources."""
        return list(self._divs.keys())

    def get_divs_ordered(self):
        """Get the divisions without the sources in chronological order from most recent."""
        if not self._ordered:
            self._order_divs()
        return self.get_divs_unordered()

    def get_divs_sourced(self) -> Dict[Division, List[SimpleSource]]:
        """Get the divisions with sources."""
        return {k: v for k, v in self._divs.items()}

    def _order_divs(self):
        self._divs = order_dict_by_value(self._divs, reverse=True)
        self._ordered = True

    @staticmethod
    def from_dict(obj: dict) -> 'DivisionsHandler':
        assert isinstance(obj, dict)
        try:
            val_dict = obj.get("Items") or obj.get("D")
            result = DivisionsHandler()
            for key, value in val_dict.items():
                result.add(Division(key), SimpleSource.from_serialized(value))
            return result
        except Exception as e:
            logging.exception(exc_info=e, msg=f"Exception occurred loading Divisions Handler: {e}, {e.args}")
            raise e

    def to_dict(self) -> dict:
        result = {}
        if len(self._divs) > 0:
            result["D"] = {k.to_serialized(): SimpleSource.to_serialized(v) for k, v in self._divs.items()}
        return result

    def __str__(self):
        return f"{self.count} Divs{(f', current={self.current_div}' if self.count > 0 else '')}"
