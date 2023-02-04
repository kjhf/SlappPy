from datetime import datetime
from os.path import join
from typing import List, Tuple, Optional, Dict

from slapp_py.core_classes.source import Source
from slapp_py.core_classes.team import Team
from slapp_py.misc.slapp_files_utils import load_latest_snapshot_sources_file, DUMPS_DIR


def get_low_ink_winners() -> Dict[Team, List[Tuple[str, str]]]:
    sources = load_latest_snapshot_sources_file()
    if not sources:
        return dict()

    teams = set([t for tournament_teams in [s.teams for s in sources] for t in tournament_teams])

    result: Dict[Team, List[Tuple[str, str]]] = dict()
    for team in teams:
        winning_placements_for_team = get_winning_low_ink_placements(team, sources)
        if winning_placements_for_team:
            result.setdefault(team, []).extend(winning_placements_for_team)

    return result


def dump_low_ink_winners_csv(teams: Dict[Team, List[Tuple[str, str]]]):
    import csv
    with open(join(DUMPS_DIR, f"{datetime.strftime(datetime.now(), '%Y-%m-%d-%H-%M-%S')}-low-ink-winners.csv"), 'w', encoding='UTF8') as f:
        writer = csv.writer(f)
        writer.writerow(["Team name", "Bracket name", "Tournament name"])
        for team, placements in teams.items():
            for placement in placements:
                writer.writerow([team, placement[0], placement[1]])


def get_winning_low_ink_placements(t: Team, sources: List[Source]) -> List[Tuple[str, str]]:
    """
    Returns the winning low inks this team has achieved, in bracket name, tournament name list form
    """
    result = []
    low_ink_sources = [s for s in sources if "low-ink-" in s.name and t.guid in list(map(lambda source_team: source_team.guid, s.teams))]

    for source in low_ink_sources:

        # Take only the winning brackets (Alpha and Top Cuts).
        # Plus the bracket must have had placements in it (a winning team)
        # We can't rely on placements that don't have one of these brackets as it may indicate that the
        # team dropped rather than was unplaced, and so is not in accordance with skill
        brackets = [b for b in source.brackets if
                    (
                            "Alpha" in b.name or
                            "Top Cut" in b.name
                    ) and 1 in b.placements.teams_by_placement]
        for bracket in brackets:
            if t.guid in bracket.placements.teams_by_placement[1]:
                result.append((bracket.name, source.name))
    return result


if __name__ == '__main__':
    dump_low_ink_winners_csv(get_low_ink_winners())
    print("Done!")
