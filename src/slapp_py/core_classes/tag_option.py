from enum import Enum


class TagOption(Enum):
    """How the Clan Tag should be rendered around a player's name."""

    Unknown = 0
    """The placements of the tag hasn't been determined"""

    Front = 1
    """Tag goes before the name"""

    Back = 2
    """Tag goes after the name"""

    Surrounding = 3
    """The tag surrounds the name, e.g. _name_"""

    Variable = 4
    """Players just do what they want sometimes"""
