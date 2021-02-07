import json
from datetime import datetime
from os.path import join
from typing import List, Dict, Optional
from uuid import UUID

from core_classes.bracket import Bracket
from core_classes.player import Player
from core_classes.skill import Skill
from misc import utils
from misc.slapp_files_utils import load_latest_snapshot_players_file, load_latest_snapshot_sources_file
from tokens import SLAPP_APP_DATA


def update_sources_with_skills(destination_sources_path: Optional[str] = None,
                               sources: Optional[List[dict]] = None,
                               players: Optional[List[Player]] = None):
    if not sources:
        sources = load_latest_snapshot_sources_file()
        assert sources, "No Sources found in the Sources snapshot file."

    if not players:
        print('Loading players...')
        players = load_latest_snapshot_players_file()
        assert players, "No Players found in the Players snapshot file."

    if not destination_sources_path:
        destination_sources_path = \
            join(SLAPP_APP_DATA, f"Snapshot-Sources-{datetime.strftime(datetime.now(), '%Y-%m-%d-%H-%M-%S')}.json")

    players_dict: Dict[UUID, Player] = {p.guid: p for p in players}

    for source in sources:
        has_changes = False
        source_name = source.get("Name", "(Unnamed source)")
        print(f'Working on {source_name}')
        for bracket_dict in source.get("Brackets", []):
            bracket: Bracket = Bracket.from_dict(bracket_dict)
            for match in bracket.matches:
                if match.score.winning_team_index != -1:
                    team1_score = match.score.points[0]
                    team2_score = match.score.points[1]
                    skills = [[players_dict[player_uuid].skill for player_uuid in match.ids[team_uuid]]
                              for team_uuid in match.ids]

                    for i in range(0, team1_score):
                        if len(match.players) == 4 and len(match.teams) == 2:
                            Skill.calculate_and_adjust_2v2(skills[0], skills[1], True)
                            has_changes = True
                        else:
                            Skill.calculate_and_adjust_4v4(skills[0], skills[1], True)
                            has_changes = True

                    for i in range(0, team2_score):
                        if len(match.players) == 4 and len(match.teams) == 2:
                            Skill.calculate_and_adjust_2v2(skills[0], skills[1], False)
                            has_changes = True
                        else:
                            Skill.calculate_and_adjust_4v4(skills[0], skills[1], False)
                            has_changes = True

        if has_changes:
            # TODO:
            #  This isn't quite right, the players snapshot needs updating, not the source, and
            #  the skills calculated need adding back in to the player object, then save that.
            print(f"Finished {source_name=}, saving to: " + destination_sources_path)
            utils.save_to_file(path=destination_sources_path,
                               content=json.dumps(sources, default=str, indent=2))
        else:
            print(f"Finished {source_name=} but no changes.")


if __name__ == '__main__':
    update_sources_with_skills()
