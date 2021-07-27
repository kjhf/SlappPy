from slapp_py.core_classes.source import Source
from slapp_py.core_classes.name import Name
from slapp_py.core_classes.team import Team

UNKNOWN_PLAYER = "(Unnamed Player)"
"""Displayed string for an unknown player."""

UNKNOWN_TEAM = "(Unnamed Team)"
"""Displayed string for an unknown team."""

BuiltinSource: Source = Source("builtin")
"""The built-in source, for use in objects that are pre-defined by the program code."""

ManualSource: Source = Source("Manual Entry")
"""The manual entry source, for use in objects that are defined by manual user entry."""

UnknownPlayerName: Name = Name(UNKNOWN_PLAYER, BuiltinSource.guid)
"""The Name for an unknown player."""

UnknownTeamName: Name = Name(UNKNOWN_TEAM, BuiltinSource.guid)
"""The Name for an unknown team."""

NoTeam = Team(names=[Name("(Free Agent)", BuiltinSource.guid)], sources=[BuiltinSource.guid])
UnknownTeam = Team(names=[UnknownTeamName], sources=[BuiltinSource.guid])
