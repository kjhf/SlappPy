import logging
from typing import TypeVar, Callable, Any, List, Union, Dict, Iterable, Mapping, Set, Optional, Type, Tuple
from uuid import UUID

T = TypeVar("T")
U = TypeVar("U")


def from_list(f: Callable[[Any], T], x: Union[None, Iterable[T], T]) -> List[T]:
    """
    Translate a serialized list into a deserialized list of objects with function f.
    If x is None or empty, an empty array is returned.

    Example:
    # Where serialized.get("Sources") would return a string or string list

    ``uuids: List[UUID] = from_list(lambda x: UUID(x), serialized.get("Sources"))``

    :param f: Callable function that returns T
    :param x: list of objects to deserialize
    :return: List of dictionaries/strings representing Ts or empty.
    """
    if not x:
        return []

    if not isinstance(x, Iterable):
        x = [x]

    if len(x) < 1:
        return []

    return [f(y) for y in x]


def to_list(f: Callable[[T], Union[dict, list, str]], x: Union[None, Iterable[T], T]) -> List[Union[dict, list, str]]:
    """
    Translate deserialized objects into a serialized list of dictionaries/strings with function f.
    If x is None or empty, an empty array is returned.

    :param f: Callable function that returns the dictionary of T
    :param x: list of objects to serialize
    :return: List of dictionaries/strings representing Ts or empty.
    """
    if not x:
        return []

    if not isinstance(x, Iterable):
        x = [x]

    if len(x) < 1:
        return []

    return [f(y) for y in x]


def serialize_uuids(uuids: Iterable[UUID]) -> List[str]:
    return list(map(lambda x: x.__str__(), uuids))


def serialize_uuids_as_dict(uuids: Mapping[Any, Iterable[UUID]]) -> Dict[str, List[str]]:
    result = dict()
    for key in uuids:
        result[key.__str__()] = serialize_uuids(uuids[key])
    return result


def deserialize_uuids(info: Mapping,
                      key: Optional[str] = None,
                      additional_maps: Iterable[Tuple[Type, Callable[[Any], UUID]]] = None) -> List[UUID]:
    """
    Read `info` dictionary at `key` for a list of uuids and deserialize them.
    If `key` is None, then the info's values/child keys will be used instead.
    Use `additional_maps` to specify any further Type to uuid conversions.
    Returns [] if key not found.
    """
    uuids: List[UUID] = []
    if not key or key == 'None':
        incoming_uuids = info
    else:
        incoming_uuids = info.get(key, [])

    if not isinstance(incoming_uuids, list):
        incoming_uuids = [incoming_uuids]

    if not incoming_uuids:
        return []

    for s in incoming_uuids:
        try:
            if not s:
                pass
            elif isinstance(s, str):
                if s == 'None':
                    continue
                uuids.append(UUID(s))
            elif isinstance(s, UUID):
                uuids.append(s)
            else:
                for mapping in additional_maps or []:
                    if isinstance(s, mapping[0]):
                        fn: Callable[[Any], UUID] = mapping[1]
                        uuids.append(fn(s))
                        continue
                logging.error(f"Could not convert s into UUID ({s=})")
        except ValueError as e:
            logging.error(f"ERROR in deserialize_uuids: {info=} with {key=}", exc_info=e)
    return uuids


def deserialize_uuids_from_dict_as_set(info: Mapping) -> Dict[Any, Set[UUID]]:
    """Read a dictionary for its top-level keys and the uuids underneath."""
    result = dict()
    for key in info:
        result[key] = set(deserialize_uuids(info, key))
    return result


def add_set_by_key(dictionary: Dict[Any, set], key: Any, values: set):
    """Add a set to a dictionary. If the set is already defined, appends the set."""
    dictionary[key] = dictionary.get(key, set()) | values


def first_key(dictionary: Mapping[T, U], default: Optional[T] = None) -> Optional[T]:
    """Get the first key of the dictionary. Completes in O(1)"""
    return next(iter(dictionary), default)
