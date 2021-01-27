from typing import TypeVar, Callable, Any, List, Union, Collection, Set, Dict, Iterable
from uuid import UUID

T = TypeVar("T")
U = TypeVar("U")


def from_list(f: Callable[[Any], T], x: Union[None, List[T], T]) -> List[T]:
    """
    Translate a serialized list into a deserialized list of objects with function f.
    If x is None or empty, an empty array is returned.

    Example:
    # Where serialized.get("Sources") would return a string or string list

    ``uuids: List[UUID] = from_list(lambda x: UUID(x), serialized.get("Sources"))``

    :param f: Callable function that returns T
    :param x: list to deserialize
    :return: List of T or empty.
    """
    if not x:
        return []

    if not isinstance(x, Iterable):
        x = [x]

    if len(x) < 1:
        return []

    return [f(y) for y in x]


def to_list(f: Callable[[T], Union[dict, str]], x: Union[None, List[T], T]) -> List[Union[dict, str]]:
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


def serialize_uuids(uuids: Collection[UUID]) -> List[str]:
    return list(map(lambda x: x.__str__(), uuids))


def deserialize_uuids(info: dict, key: str, default=None) -> List[UUID]:
    return from_list(lambda x: UUID(x), info.get(key, default))


def add_set_by_key(dictionary: Dict[Any, Set], key: Any, values: Set):
    dictionary[key] = dictionary.get(key, set()) | values
