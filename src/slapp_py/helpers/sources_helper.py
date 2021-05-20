import re
from typing import List, Dict, Optional

from slapp_py.helpers.str_helper import truncate, escape_characters


def truncate_source(source: str, max_length: int = 128) -> str:
    # Strip the source id
    source = re.sub("-+[0-9a-fA-F]+$", '', source)
    source = escape_characters(source)

    # Truncate
    source = truncate(source, max_length, '…')
    return source


def attempt_link_source(source_name: Optional[str]) -> str:
    """Take a source and attempt to convert it into a link"""

    if not source_name:
        return source_name

    # Mapping takes a list of tournament names and gives an organisation name
    mapping: Dict[str, List[str]] = {
        'inkling-performance-labs': ['-low-ink-', '-testing-grounds-' '-swim-or-sink-'],
        'inktv': ['-bns-', '-swl-winter-snowflake-', '-splatoon-world-league-',
                  '-inktv-open-', '-extrafaganza-', '-inkvitational-'],
        'sitback-saturdays': ['-sitback-saturdays-'],
        'splatoon2': ['-splatoon-2-north-american-online-open-'],
        'squidboards-splatoon-2-community-events': ['-sqss-', '-squidboards-splat-series-'],
        'squid-spawning-grounds': ['-squid-spawning-grounds-'],
        'fresh-start-cup': ['-fresh-start-cup-'],
        'swift-second-saturdays': ['-sss-'],
        'gamesetmatch': ['-gsm-'],
        'area-cup': ['-area-cup-'],
        'asquidmin': ['-turtlement-'],
    }

    for organiser in mapping:
        for tourneys in mapping[organiser]:
            for tournament_name in tourneys:
                if tournament_name in source_name:
                    m = re.search("-+([0-9a-fA-F]+)$", source_name, re.I)
                    text = truncate_source(source_name)
                    if m:
                        guid = m.groups()[0]
                        return f'[{text}](https://battlefy.com/{organiser}//{guid}/info)'
                    else:
                        return text
    return truncate_source(source_name)
