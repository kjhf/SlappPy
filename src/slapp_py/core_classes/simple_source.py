import functools
import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, AnyStr, Union

from slapp_py.helpers.str_helper import truncate, escape_characters

# Mapping takes a list of tournament names and gives an organisation name
SOURCE_ORGANISER_MAPPING: Dict[str, List[str]] = {
    'area-cup': ['-area-cup-'],
    'asquidmin': ['-turtlement-'],
    'deep-sea-solutions': ['megalodon-cup-', '-minnow-cup-', 'trick-no-treat'],
    'fresh-start-cup': ['-fresh-start-cup-'],
    'gamesetmatch': ['-gsm-'],
    'inkling-performance-labs': ['-low-ink-', '-testing-grounds-', '-swim-or-sink-'],
    'inktv': ['-bns-', '-swl-winter-snowflake-', '-splatoon-world-league-', '-inktv-open-', '-extrafaganza-', '-inkvitational-'],
    'jerrys-crown-cup': ['-jerrys-crown-cup-'],
    'jpgs-questionable-tournaments': ['fastest-event-in-the-west-'],
    'little-squid-league': ['-little-squid-league-', '-little-squid-league-invitational-'],
    'midway-ink-tour': ['-midway-'],
    'sitback-saturdays': ['-sitback-saturdays-'],
    'splatcom': ['-armas-random-', '-duelos-', '-dúos-dittos-', 'splatcom-', '-suizo-latino-', '-torneo-de-', '-torneo-festivo-'],
    'splatoon2': ['-splatoon-2-north-american-online-open-'],
    'splatoon-amateur-circuit': ['-sac-tournament-', '-season-3-tournament-3-youre-an', '-season-3-tournament-2-hey-now'],
    'squid-junction': ['squid-junction-'],
    'squid-south': ['squid-south-2v2-', '-squid-souths-halloween-2v2-'],
    'squid-spawning-grounds': ['-squid-spawning-grounds-'],
    'squidboards-splatoon-2-community-events': ['-sqss-', '-squidboards-splat-series-'],
    'swift-second-saturdays': ['-sss-'],
    'ultimate-splat-championship': ['-usc-'],
}

TOURNAMENT_ID_REGEX = re.compile("-+([0-9a-fA-F]{18,})$", re.I)


@dataclass(frozen=True)
class SimpleSource:
    """
    Simple Source is a string representation of a Source which can break the serialization references chain.
    Previously represented as a GUID, but a string fulfils this requirement and can be ordered by date and name.
    """
    name: str = field(init=True, compare=False, hash=True)
    """The full name of the source"""
    date: str = field(init=False, compare=True)
    """The date part of the source, e.g. 1970-01-31"""
    organiser: Optional[str] = field(init=False, compare=False)
    """The organiser part of the source, e.g. IPL"""
    tournament_name: Optional[str] = field(init=False, compare=False)
    """The tournament name part of the source, e.g. low-ink-january"""
    tournament_id: Optional[str] = field(init=False, compare=False)
    """The tournament id part of the source, which is a hexadecimal id complying to TOURNAMENT_ID_REGEX"""

    def __post_init__(self):
        # Name has been set in the dataclass __init__
        (date, organiser, tournament_name, tournament_id) = self._initialise(self.name)
        # These mutations are needed as the dataclass is frozen.
        super().__setattr__('date', date)
        super().__setattr__('organiser', organiser)
        super().__setattr__('tournament_name', tournament_name)
        super().__setattr__('tournament_id', tournament_id)

    @property
    def id(self):
        """Returns the source's name."""
        return self.name

    @property
    def url(self):
        """Returns the source's URL as a Battlefy link."""
        return f"https://battlefy.com/_/_/{self.tournament_id}/info" if self.tournament_id else None

    def __str__(self):
        """Overridden - returns the source's name."""
        return self.name

    def __lt__(self, other): return (self.date < other.date) if (self.date and other.date) else (self.name < other.name)
    def __le__(self, other): return (self.date <= other.date) if (self.date and other.date) else (self.name <= other.name)
    def __eq__(self, other): return (self.date == other.date) if (self.date and other.date) else (self.name == other.name)
    def __ne__(self, other): return (self.date != other.date) if (self.date and other.date) else (self.name != other.name)
    def __gt__(self, other): return (self.date > other.date) if (self.date and other.date) else (self.name > other.name)
    def __ge__(self, other): return (self.date >= other.date) if (self.date and other.date) else (self.name >= other.name)

    @staticmethod
    @functools.cache
    def _initialise(source_name: Optional[str]) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        """Initialise the simple source's (date, organiser, tournament name, tournament id)."""
        if not source_name:
            return None, None, None, None

        if len(source_name) > 11 and source_name.count('-') > 2:
            date = source_name[0:10].strip('- ')
            default_tourney_name = source_name[11:].strip('- ')
        else:
            date = None
            default_tourney_name = source_name

        id_at_the_end_match = TOURNAMENT_ID_REGEX.search(source_name)
        if id_at_the_end_match:
            # We always want to grab the last match as the id is at the end of the source name.
            tournament_id = id_at_the_end_match.groups()[-1]
            default_tourney_name = TOURNAMENT_ID_REGEX.sub('', default_tourney_name, count=1)
        else:
            tournament_id = None

        for organiser, tourneys in SOURCE_ORGANISER_MAPPING.items():
            for tournament_name in tourneys:
                if tournament_name in source_name:
                    return date, organiser.strip('- '), tournament_name.strip('- '), tournament_id
        else:
            tournament_name = default_tourney_name

            # Try and get the organiser from the ORG_SLUGS list.
            try:
                from battlefy_toolkit.org_lists.splatoon_orgs import ORG_SLUGS as _SLUGS
            except ImportError:
                _SLUGS = []
                pass

            for organiser in _SLUGS:
                if f"-{organiser}-" in source_name:
                    tournament_name = tournament_name.replace(f"-{organiser}-", '').strip('- ')
                    return date, organiser.strip('- '), tournament_name, tournament_id

            return date, None, tournament_name, tournament_id

    def get_linked_date_display(self) -> str:
        """Return a markdown link with the truncated source date if available,
        otherwise return its truncated_name only."""
        link = self.url
        if self.date:
            text = truncate(escape_characters(self.date), 16)
        else:
            text = self.truncated_name
        return f"[{text}]({link})" if link else text

    def get_linked_name_display(self) -> str:
        """Return a markdown link with the truncated source name (date-name) if available,
        otherwise return its truncated_name only."""
        link = self.url
        text = self.truncated_name
        return f"[{text}]({link})" if link else text

    @property
    def truncated_name(self):
        """The source with the id removed and truncated down."""
        if self.date and self.tournament_name:
            display_name = self.date + '-' + self.tournament_name
        else:
            display_name = self._strip_source_id(self.name)
        return truncate(escape_characters(display_name), 100)

    @staticmethod
    def _strip_source_id(source: AnyStr) -> str:
        """Strip the source id from the source"""
        return TOURNAMENT_ID_REGEX.sub('', source)

    @staticmethod
    def to_serialized(sources: Union[None, List[Union[str, 'SimpleSource']], str, 'SimpleSource']) -> Union[None, str, List[str]]:
        if not sources:
            return None
        elif isinstance(sources, str):
            return sources
        elif isinstance(sources, list):
            return list({val.__str__() for val in sorted(sources, reverse=True)})
        elif isinstance(sources, SimpleSource):
            return sources.__str__()
        else:
            logging.error(f"Cannot serialize SimpleSource from {type(sources)=} {sources=}")
            return None

    @staticmethod
    def from_serialized(obj: Union[List[Union[str, 'SimpleSource']], Dict[str, str], str, 'SimpleSource']) -> Optional[List['SimpleSource']]:
        """
        Translate serialized forms into a list of SimpleSources.
        Returns None if a bad single form (None, empty, 'null' etc) is passed in.
        """
        result: List['SimpleSource'] = []
        if obj is None:
            return None
        elif isinstance(obj, str) or isinstance(obj, SimpleSource):
            val = SimpleSource._from_serialized_single(obj)
            return [val] if val else val
        elif isinstance(obj, list):
            if obj:
                for val in obj:
                    el = SimpleSource._from_serialized_single(val)
                    if el:
                        result.append(el)
        elif isinstance(obj, dict):
            # Old form. We don't care what the key is (it's either "S" for source, or its id).
            result = []
            if obj:
                for _, v in obj.items():
                    el = SimpleSource._from_serialized_single(v)
                    if el:
                        result.append(el)
        else:
            logging.error(f"Cannot deserialize SimpleSource from {type(obj)=} {obj=}")
        return result

    @staticmethod
    def _from_serialized_single(obj: Union[str, 'SimpleSource']) -> Optional['SimpleSource']:
        if obj is None:
            return None
        elif isinstance(obj, str):
            if not obj or obj.lower() in ('none', 'null'):
                return None
            return SimpleSource(obj)
        elif isinstance(obj, SimpleSource):
            return obj
        else:
            logging.error(f"Cannot deserialize single SimpleSource from {type(obj)=} {obj=}")
            return None
