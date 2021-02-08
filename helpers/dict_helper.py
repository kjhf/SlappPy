from typing import TypeVar, Callable, Any, List, Union, Dict, Iterable, Mapping
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


def to_list(f: Callable[[T], Union[dict, str]], x: Union[None, Iterable[T], T]) -> List[Union[dict, str]]:
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


def deserialize_uuids(info: Mapping, key: str, default=None) -> List[UUID]:
    """Read a dictionary at the key for a list of uuids and deserialize them.
    Returns a default if the key is not found."""
    return from_list(lambda x: UUID(x), info.get(key, default))


def deserialize_uuids_from_dict(info: Mapping) -> Dict[Any, List[UUID]]:
    """Read a dictionary for its top-level keys and the uuids underneath."""
    result = dict()
    for key in info:
        result[key] = deserialize_uuids(info, key)
    return result


def add_set_by_key(dictionary: Dict[Any, set], key: Any, values: set):
    """Add a set to a dictionary. If the set is already defined, appends the set."""
    dictionary[key] = dictionary.get(key, set()) | values


def first_key(dictionary: Mapping[T, U]) -> T:
    """Get the first key of the dictionary. Completes in O(1)"""
    return next(iter(dictionary))
