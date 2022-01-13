from slapp_py.core_classes import name, team

NO_SOURCE = "0001-01-01-No-Source-Specified"
"""No source name for builtins and unknowns."""

UNKNOWN_PLAYER = "(Unnamed Player)"
"""Displayed string for an unknown player."""

UNKNOWN_TEAM = "(Unnamed Team)"
"""Displayed string for an unknown team."""

UnknownPlayerName = name.Name(UNKNOWN_PLAYER)
"""The Name for an unknown player."""

UnknownTeamName = name.Name(UNKNOWN_TEAM)
"""The Name for an unknown team."""

NoTeam = team.Team(names=name.Name("(Free Agent)"))
UnknownTeam = team.Team(names=UnknownTeamName)
