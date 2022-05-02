import asyncio
import glob
import json
from datetime import datetime
from os.path import join, relpath
from typing import Set, Optional, Collection, Tuple, Dict, Union, Iterable, List, Any
from uuid import UUID

from battlefy_toolkit.caching.fileio import save_as_json_to_file, save_text_to_file
from battlefy_toolkit.downloaders.tourney_downloader import get_or_fetch_tourney_ids
from battlefy_toolkit.utils.misc import assert_is_dict_recursive

from slapp_py.core_classes.bracket import Bracket
from slapp_py.core_classes.game import Game
from slapp_py.core_classes.player import Player
from slapp_py.core_classes.score import Score
from slapp_py.core_classes.source import Source
from slapp_py.core_classes.team import Team
from slapp_py.helpers.battlefy_helper import is_valid_battlefy_id, filter_non_battlefy_source
from slapp_py.helpers.dict_helper import first_key, add_set_by_key
from slapp_py.helpers.str_helper import is_none_or_whitespace
from slapp_py.misc.download_from_battlefy_result import get_or_fetch_tourney_teams_file, get_stage_ids_for_tourney, \
    get_or_fetch_stage_file, get_or_fetch_standings_file
from slapp_py.misc.download_from_sendou import conditionally_download_from_sendou_and_save
from slapp_py.misc.slapp_files_utils import TOURNEY_TEAMS_SAVE_DIR, get_latest_sources_yaml_file, \
    load_latest_snapshot_sources_file, load_latest_snapshot_players_file, get_slapp_files_matching
from slapp_py.slapp_runner.slapipes import SLAPP_DATA_FOLDER, SlapPipe


async def _receive_slapp_response(success_message: str, response: dict):
    print("Success: " + success_message + ", dict: " + json.dumps(response))


def load_sources_yaml_file(path: Optional[str] = None):
    """
    Load the yaml sources file - this is in the format of one source file to load per line.
    :param path: The sources file path. Do not specify to use the latest default.
    :return: The contents of the sources file - expected a list of source file paths.
    If the file path doesn't exist, None is returned.
    """
    if not path:
        path = get_latest_sources_yaml_file()
    try:
        with open(path, 'r', encoding='utf-8') as infile:
            return infile.read().split('\n')
    except (TypeError, OSError):
        return None


def fetch_tournament_ids(save_path: Optional[str] = None) -> Set[str]:
    """
    Fetch the latest tournament ids from Battlefy.
    :param save_path: Optionally save to a (json) file by specifying a path.
    :returns The set of tournament ids for processing.
    """

    print("Fetching tourney ids...")
    full_tourney_ids = get_or_fetch_tourney_ids()

    print(f"Getting tourneys from the ids ({len(full_tourney_ids)} to get)")
    for tourney_id in full_tourney_ids:
        _ = get_or_fetch_tourney_teams_file(tourney_id)

    if save_path:
        print("Saving...")
        save_as_json_to_file(save_path, list(full_tourney_ids))
    return full_tourney_ids


def generate_new_sources_files(battlefy_ids: Collection[str], skip_redownload: bool = False) -> Tuple[str, str]:
    """
    Take the collection of (new) battlefy ids and generate a new sources file and a patch file.
    :param battlefy_ids: Collection of (new) battlefy ids to process.
    :param skip_redownload: Skip the redownload of files if a failure has occurred?
    :returns: A tuple containing the file path to the new sources file, and new patch file.
    """

    # Current sources:
    sources_contents = load_sources_yaml_file() or []
    battlefy_ids_len = len(battlefy_ids)
    print(f"{len(sources_contents)} sources loaded from current sources yaml. "
          f"{battlefy_ids_len} Battlefy Ids known. (Diff of {battlefy_ids_len - len(sources_contents)}).")

    # Sources now that we've pulled in the tourney files:
    # Dictionary keyed by ids with values of path,
    # and if the source is new since the current source (true) or was present in the last sources file (false)
    processed_tourney_ids: Dict[str, Tuple[str, bool]] = {}
    for tourney_id in battlefy_ids:
        # Search the sources yaml
        filename = tourney_id + ".json"
        found_line = next((line for line in sources_contents if line.endswith(filename)), None)

        if found_line:
            # Not new
            processed_tourney_ids[tourney_id] = (found_line, False)
        else:
            # New
            matched_tourney_teams_files = glob.glob(join(TOURNEY_TEAMS_SAVE_DIR, f'*{filename}'))
            if len(matched_tourney_teams_files) == 1:
                relative_path = relpath(matched_tourney_teams_files[0], start=SLAPP_DATA_FOLDER)
                if not relative_path.startswith('.'):
                    relative_path = './' + relative_path
                processed_tourney_ids[tourney_id] = (relative_path, True)
            else:
                print(f"ERROR: Found an updated tourney file but a unique file wasn't downloaded for it: "
                      f"{tourney_id=}, {len(matched_tourney_teams_files)=}")
                if skip_redownload:
                    continue
                else:
                    print("Re-attempting download...")
                    if get_or_fetch_tourney_teams_file(tourney_id):
                        print("Success!")
                        matched_tourney_teams_files = glob.glob(join(TOURNEY_TEAMS_SAVE_DIR, f'*{filename}'))
                        if len(matched_tourney_teams_files) == 1:
                            relative_path = relpath(matched_tourney_teams_files[0], start=SLAPP_DATA_FOLDER)
                            processed_tourney_ids[tourney_id] = (relative_path, True)
                        else:
                            print(f"ERROR: Reattempt failed. Please debug. "
                                  f"{tourney_id=}, {len(matched_tourney_teams_files)=}")
                    else:
                        print(f"ERROR: Reattempt failed. Skipping file. "
                              f"{tourney_id=}, {len(matched_tourney_teams_files)=}")

    # And the other json or tsv data files
    additional_files = []
    conditionally_download_from_sendou_and_save()
    additional_files.extend(get_slapp_files_matching('*-*-*-*.json', TOURNEY_TEAMS_SAVE_DIR))
    additional_files.extend(get_slapp_files_matching('*-*-*-*.tsv', TOURNEY_TEAMS_SAVE_DIR))

    for additional_file in additional_files or []:
        relative_path = relpath(additional_file, start=SLAPP_DATA_FOLDER)
        if not relative_path.startswith('.'):
            relative_path = './' + relative_path
        relative_path = relative_path.replace('\\', '/')
        found_line = next((line for line in sources_contents if line.replace('\\', '/').endswith(relative_path)), None)
        is_new = not found_line
        if found_line:
            # Not new
            processed_tourney_ids[additional_file] = (found_line, False)
        else:
            processed_tourney_ids[additional_file] = (relative_path, True)
        print(f"{additional_file=}, {SLAPP_DATA_FOLDER=}, {relative_path=}, {is_new=}")

    # Now update the yaml
    print(f"Updating the yaml ({len(sources_contents)} sources).")

    # Take care of those pesky exceptions to the rule
    # statink folder is special
    if sources_contents and './statink' in sources_contents:
        statink_present = True
        sources_contents.remove('./statink')
    else:
        statink_present = False

    # Twitter goes last (but only if not dated)
    if sources_contents and 'Twitter.json' in sources_contents[-1]:
        twitter_str = sources_contents[-1]
        sources_contents.remove(sources_contents[-1])
    else:
        twitter_str = None

    # Add in the new updates
    patch_sources_contents = []
    for updated_id in processed_tourney_ids:
        path, is_new = processed_tourney_ids[updated_id]
        if is_new:
            sources_contents.append(path)
            patch_sources_contents.append(path)

    # Replace backslashes with forwards
    print(f"Fixing backslashes... ({len(sources_contents)} sources).")
    sources_contents = [line.replace('\\', '/') for line in sources_contents]
    patch_sources_contents = [line.replace('\\', '/') for line in patch_sources_contents]

    # Distinct & sort.
    print(f"Sorting and filtering... ({len(sources_contents)} sources).")
    sources_contents = list(set(sources_contents))
    patch_sources_contents = list(set(patch_sources_contents))
    sources_contents.sort()
    patch_sources_contents.sort()

    # Add the exceptions back in to the correct places
    # To the start (which will be second if undated Sendou is present)
    if statink_present:
        sources_contents.insert(0, './statink')

    # To the end
    if twitter_str:
        sources_contents.append(twitter_str)

    # Remove blank lines
    print(f"Removing blanks... ({len(sources_contents)} sources).")
    sources_contents = [line for line in sources_contents if not is_none_or_whitespace(line)]

    print(f"Writing to sources_new.yaml... ({len(sources_contents)} sources).")
    new_sources_file_path = join(SLAPP_DATA_FOLDER, 'sources_new.yaml')
    save_text_to_file(path=new_sources_file_path,
                      content='\n'.join(sources_contents))

    print(f"Writing to sources_patch.yaml... ({len(patch_sources_contents)} sources).")
    patch_sources_file_path = join(SLAPP_DATA_FOLDER, 'sources_patch.yaml')
    save_text_to_file(path=patch_sources_file_path,
                      content='\n'.join(patch_sources_contents))

    print(f"generate_new_sources_files complete, "
          f"{len(sources_contents)} sources written with {len(processed_tourney_ids)} processed ids, "
          f"of which {len(patch_sources_contents)} are new.")
    return new_sources_file_path, patch_sources_file_path


def _invoke_slapp(command: str):
    loop = asyncio.get_event_loop()
    print("Calling " + command)

    slappipe = SlapPipe()
    loop.run_until_complete(
        asyncio.gather(
            slappipe.initialise_slapp(_receive_slapp_response, command)
        )
    )


def rebuild_sources(new_sources_file_path, verbose: bool = True):
    _invoke_slapp(f"{'--verbose ' if verbose else ''}--rebuild {new_sources_file_path}")


def patch_sources(new_sources_file_path, verbose: bool = True):
    _invoke_slapp(f"{'--verbose ' if verbose else ''}--patch {new_sources_file_path}")


_global_player_local_id_to_slapp_id = dict()


def player_local_id_to_slapp_id(_local_player_id: Union[str, UUID],
                                _player_id_to_persistent_id: Dict[str, str],
                                _players: Iterable[Player]) -> Optional[UUID]:
    global _global_player_local_id_to_slapp_id
    if _local_player_id in _global_player_local_id_to_slapp_id:
        return _global_player_local_id_to_slapp_id[_local_player_id]

    # Search for the persistent id for this player.
    _persistent_id = _player_id_to_persistent_id.get(_local_player_id.__str__())
    if _persistent_id:
        slapp_id = player_persistent_id_to_slapp_id(_persistent_id, _players)
        _global_player_local_id_to_slapp_id[_local_player_id] = slapp_id
        return slapp_id
    else:
        # print(f'Could not translate local player ID ({_local_player_id})'
        #       f' into a persistent Player Id.'
        #       # f'_player_id_to_persistent_id={", ".join(_player_id_to_persistent_id.keys())}')
        return None


_global_player_persistent_id_to_slapp_id = dict()


def player_persistent_id_to_slapp_id(_persistent_player_id: Union[str, UUID],
                                     _players: Iterable[Player]) -> Optional[UUID]:
    global _global_player_persistent_id_to_slapp_id
    if isinstance(_persistent_player_id, UUID):
        _persistent_player_id = _persistent_player_id.__str__()

    if _persistent_player_id in _global_player_persistent_id_to_slapp_id:
        return _global_player_persistent_id_to_slapp_id[_persistent_player_id]

    # Search for the Slapp record of this player.
    _found_player = next(
        (player_in_source for player_in_source in _players
         if _persistent_player_id in player_in_source.battlefy.battlefy_persistent_id_strings), None)
    if _found_player:
        _global_player_persistent_id_to_slapp_id[_persistent_player_id] = _found_player.guid.__str__()
        return _found_player.guid
    else:
        print(f'Could not translate persistentPlayerID ({_persistent_player_id}) '
              f'into a Slapp Player Id.')
        return None


def team_persistent_id_to_slapp_id(_persistent_team_id: Union[str, UUID], _teams: Iterable[Team]) -> Optional[UUID]:
    # Search for the Slapp record of this team.
    _found_team = next(
        (team_in_source for team_in_source in _teams
         if _persistent_team_id.__str__() in team_in_source.battlefy_persistent_id_strings), None)
    if _found_team:
        return _found_team.guid
    else:
        print(f'Could not translate persistentTeamID ({_persistent_team_id}) '
              f'into a Slapp Team Id.')
        return None


def get_source_by_tourney_id(tourney_id: str,
                             sources: List[Source]) -> Optional[Source]:
    return next((s for s in sources if s.tournament_id == tourney_id), None)


def add_tourney_placement_to_source(tourney_id: str,
                                    players: Iterable[Player],
                                    sources: List[Source]) -> bool:
    stage_ids = {stage_id for stage_id in get_stage_ids_for_tourney(tourney_id)
                 if is_valid_battlefy_id(stage_id)}
    if len(stage_ids) == 0:
        print(f'No stages found in {tourney_id=}.')
        return False

    # Find the suitable source in the latest sources snapshot
    source = get_source_by_tourney_id(tourney_id, sources)
    if not source:
        print(f"Could not find a source in the snapshot that matches {tourney_id=}. Not adding.")
        return False

    if source.brackets and source.brackets[0].is_valid and source.brackets[-1].is_valid:
        print(f"Brackets already exist for this source. Skipping.")
        return False

    _global_player_local_id_to_slapp_id.clear()

    # For each stage, translate the stage bracket into a Bracket object
    for stage_id in stage_ids:
        stage_contents = get_or_fetch_stage_file(tourney_id, stage_id, force=False)
        if not stage_contents:
            continue

        bracket: Bracket = Bracket(name=stage_contents["name"])

        # We can get the relevant team from the sources file and matching against battlefy persistent team id
        # For now, let's store the teams in the bracket information - we'll have to convert them later.
        player_id_to_persistent_id_lookup = dict()
        for match in stage_contents["matches"]:
            if match["isBye"]:
                continue

            team_result_1 = match.get("top")
            team_result_2 = match.get("bottom")

            if not team_result_1 or not team_result_2:
                print(f"Incomplete team result top/bottom, see {match=}")
                continue

            team1 = team_result_1.get("team")
            team2 = team_result_2.get("team")

            if not team1 or not team2:
                print(f"Incomplete team data, see {team_result_1=} or {team_result_2=}")
                continue

            if "persistentTeamID" not in team1 or "persistentTeamID" not in team2:
                print(f"Incomplete team: persistentTeamID not defined. {team_result_1=} or {team_result_2=}")
                continue

            team1_slapp_id = team_persistent_id_to_slapp_id(team1["persistentTeamID"], source.teams) or None
            team1_player_slapp_ids = []
            for player_dict in team1.get("players", []):
                player_persistent_id = player_dict.get("persistentPlayerID")  # else None
                if player_persistent_id:
                    team1_player_slapp_ids.append(player_persistent_id_to_slapp_id(player_persistent_id, players))
                    player_id_to_persistent_id_lookup[player_dict["_id"]] = player_persistent_id
                else:
                    print(f"Skipping player in {json.dumps(player_dict)} - there's no persistentPlayerID.")

            team2_slapp_id = team_persistent_id_to_slapp_id(team2["persistentTeamID"], source.teams) or None
            team2_player_slapp_ids = []
            for player_dict in team2.get("players", []):
                player_persistent_id = player_dict.get("persistentPlayerID")  # else None
                if player_persistent_id:
                    team2_player_slapp_ids.append(player_persistent_id_to_slapp_id(player_persistent_id, players))
                    player_id_to_persistent_id_lookup[player_dict["_id"]] = player_persistent_id
                else:
                    print(f"Skipping player in {json.dumps(player_dict)} - there's no persistentPlayerID.")

            if team1_slapp_id and team2_slapp_id:
                ids_dictionary = {
                    team1_slapp_id: team1_player_slapp_ids,
                    team2_slapp_id: team2_player_slapp_ids,
                }
                game = Game(score=Score([team_result_1.get("score", -1), team_result_2.get("score", -1)]),
                            ids=ids_dictionary)
                bracket.matches.append(game)
            else:
                print(f"Skipping game in {json.dumps(match)} - the team(s) were not matched to Slapp ids.")

            # Loop to next match

        # Add placements
        standings_contents = get_or_fetch_standings_file(tourney_id, stage_id, force=False)
        if standings_contents:
            # If place is present (i.e. for finals), order by that.
            standings_placements = {}

            first_node = first_key(standings_contents)
            if isinstance(first_node, str):
                first_node = standings_contents[first_node]

            if first_node.get('place', False):
                standings_placements = \
                    sorted(standings_contents,
                           key=lambda k:
                           (
                               int(k.get("place", 99999)),
                               k.get("team", {}).get("name", '')
                           ))

            # Otherwise, work out the order:
            #  1. The team's match wins ["matchWinPercentage"]
            #  2. The opponent's match win percentage ["opponentsMatchWinPercentage"]
            #  3. The team's game win percentage ["gameWinPercentage"]
            #  4. The opponent's opponent's match win percentage ["opponentsOpponentsMatchWinPercentage"]
            elif first_node.get('matchWinPercentage') \
                    and first_node.get('opponentsMatchWinPercentage') \
                    and first_node.get('gameWinPercentage') \
                    and first_node.get('opponentsOpponentsMatchWinPercentage'):
                standings_placements = sorted(standings_contents,
                                              key=lambda k:
                                              (
                                                  int(k.get("matchWinPercentage", -1) or -1),
                                                  int(k.get("opponentsMatchWinPercentage", -1) or -1),
                                                  int(k.get("gameWinPercentage", -1) or -1),
                                                  int(k.get("opponentsOpponentsMatchWinPercentage", -1) or -1)
                                              ), reverse=True)
            else:
                print(f'ERROR: Skipping calculation of placements as this node does not have '
                      f'the required fields: {json.dumps(first_node)}')

            for i, standing_node in enumerate(standings_placements):
                place = (i + 1)
                standing_node: Dict[str, Any]

                add_set_by_key(dictionary=bracket.placements.players_by_placement,
                               key=place,
                               values={
                                   player_local_id_to_slapp_id(
                                       _local_player_id=local_id,
                                       _player_id_to_persistent_id=player_id_to_persistent_id_lookup,
                                       _players=players
                                   ) or ''
                                   for local_id in standing_node.get("team", {}).get("playerIDs", [])
                               })
                bracket.placements.players_by_placement[place].discard('')

                add_set_by_key(dictionary=bracket.placements.teams_by_placement,
                               key=place,
                               values={
                                   team_persistent_id_to_slapp_id(
                                       _persistent_team_id=standing_node.get("team", {}).get("persistentTeamID", ''),
                                       _teams=source.teams)
                                   or ''
                               })
                bracket.placements.teams_by_placement[place].discard('')

        # Add to the Source
        source.brackets.append(bracket)

    # Finish up
    # Save the snapshot file
    dict_to_save = source.to_dict()
    assert_is_dict_recursive(dict_to_save)
    return True


def update_sources_with_placements(tourney_ids: Optional[Collection[str]] = None,
                                   destination_sources_path: Optional[str] = None,
                                   sources: Optional[List[Source]] = None,
                                   players: Optional[List[Player]] = None):
    """
    Updates a sources list with placements for the players from the specified tournament ids.
    :param tourney_ids: The tournament ids to process.
    :param destination_sources_path: File path to save to. If None, uses a default Sources location.
    :param sources: Sources to process. If None, uses the latest Sources snapshot file.
    :param players: Players to process. If None, uses the latest Players snapshot file.
    :return:
    """

    if not sources:
        print('Loading sources...')
        sources = load_latest_snapshot_sources_file()
        assert sources, "No Sources found in the Sources snapshot file."

    if not players:
        print('Loading players...')
        players = load_latest_snapshot_players_file()
        assert players, "No Players found in the Players snapshot file."

    if not tourney_ids:
        tourney_ids = {source.tournament_id for source in sources
                       if not source.brackets
                       and filter_non_battlefy_source(source.name)}

    if not destination_sources_path:
        destination_sources_path = \
            join(SLAPP_DATA_FOLDER, f"Snapshot-Sources-{datetime.strftime(datetime.now(), '%Y-%m-%d-%H-%M-%S')}.json")

    # Filter ids that are less than 20 characters or more than 30 (id is probably not correct) --
    # expected 24 chars, and hex numbers only.
    original_count = len(tourney_ids)
    tourney_ids = {tourney_id for tourney_id in tourney_ids if is_valid_battlefy_id(tourney_id)}
    actual_count = len(tourney_ids)
    if original_count != actual_count:
        print(f'Some ids were filtered as they were invalid ({original_count} -> {len(tourney_ids)})')

    for i, tourney_id in enumerate(tourney_ids):
        print(f'[{i+1}/{actual_count}] Working on {tourney_id=}')
        has_changes = add_tourney_placement_to_source(tourney_id, players, sources)
        if has_changes:
            print(f"Finished {tourney_id=}, changes made.")
        else:
            print(f"Finished {tourney_id=} but no changes.")

    print(f"Update sources with placements done, saving sources to: " + destination_sources_path)
    save_as_json_to_file(destination_sources_path, [source.to_dict() for source in sources], indent=0)
