import logging
from typing import TypeVar, Callable, Any, List, Union, Dict, Iterable, Mapping, Set, Optional, Tuple, Type
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


def deserialize_uuids_into_list(incoming_uuids: Union[UUID, str, Iterable[Union[str, UUID]]],
                                additional_maps: Iterable[Tuple[Type, Callable[[Any], UUID]]] = None) -> List[UUID]:
    """
    Read the incoming_uuids for a list of uuids and deserialize them by converting from str or constructing
    a list as necessary. Empties and Nones are removed.
    Use `additional_maps` to specify any further Type to uuid conversions.
    :raises ValueError: A string was specified but is not a UUID.
    """
    uuids: List[UUID] = []

    if not isinstance(incoming_uuids, list):
        incoming_uuids = [incoming_uuids]

    if not incoming_uuids:
        return []

    for val in incoming_uuids:
        if val is None:
            pass
        elif isinstance(val, str):
            if not val or val.lower() in ('none', 'null'):
                continue
            uuids.append(UUID(val))
        elif isinstance(val, UUID):
            uuids.append(val)
        else:
            for mapping in additional_maps or []:
                if isinstance(val, mapping[0]):
                    fn: Callable[[Any], UUID] = mapping[1]
                    uuids.append(fn(val))
                    break
            else:
                logging.error(f"deserialize_uuids_into_list: Could not convert {val=} of {type(val)=} into a UUID")
    return uuids


def deserialize_uuids(info: Mapping,
                      key: Optional[str] = None,
                      additional_maps: Iterable[Tuple[Type, Callable[[Any], UUID]]] = None) -> List[UUID]:
    """
    Read the `info` dictionary at `key` for a list of uuids and deserialize them.
    If `key` is None, then the info's values/child keys will be used instead.
    Returns [] if key not found.
    """
    if not key or key == 'None':
        incoming_uuids = info
    else:
        incoming_uuids = info.get(key, [])

    try:
        uuids = deserialize_uuids_into_list(incoming_uuids, additional_maps)
    except ValueError as e:
        logging.error(f"deserialize_uuids: Error in {info=} with {key=}", exc_info=e)
        uuids = []
    return uuids


def deserialize_uuids_from_dict_as_set(info: Mapping,
                                       additional_maps: Iterable[Tuple[Type, Callable[[Any], UUID]]] = None) -> Dict[Any, Set[UUID]]:
    """Read a dictionary for its top-level keys and the uuids underneath."""
    result = dict()
    for key in info:
        result[key] = set(deserialize_uuids(info, key, additional_maps))
    return result


def add_set_by_key(dictionary: Dict[Any, set], key: Any, values: set):
    """Add a set to a dictionary. If the set is already defined, appends the set."""
    dictionary[key] = dictionary.get(key, set()) | values


def first_key(dictionary: Mapping[T, U], default: Optional[T] = None) -> Optional[T]:
    """Get the first key of the dictionary. Completes in O(1)"""
    return next(iter(dictionary), default)


def key_value_list_to_dict(kv_list: List[tuple]) -> Dict[Any, list]:
    """
    Transform a list of key-value KV tuples into a dictionary.
    If KV tuples exist where the keys are duplicated, the value is added to the first key's list.
    """
    d = {}
    for k, v in kv_list:
        # DefaultDict
        d.setdefault(k, []).append(v)
    return d


def order_dict_by_value(dictionary: Mapping[T, U], reverse: bool = False) -> Dict[T, U]:
    """
    Orders a dictionary by its values. Reverse is passed to the sorted builtin.
    If the value is a List, a min (reverse=False) or max (reverse=True) is performed on the values
    and its result is used in the ordering.
    """
    return dict(sorted(dictionary.items(),
                       key=lambda item:
                           (max(item[1]) if reverse else min(item[1])) if isinstance(item[1], list)
                           else item[1],
                       reverse=reverse))
