import glob
import json
from datetime import datetime
from os import makedirs
from os.path import exists, isfile, join
from typing import Optional

import challonge  # pychal
from caching.fileio import save_as_json_to_file, load_json_from_file  # battlefy-toolkit

from misc.slapp_files_utils import TOURNEY_INFO_SAVE_DIR, TOURNEY_TEAMS_SAVE_DIR, STAGES_SAVE_DIR
from tokens import CHALLONGE_API_KEY, CHALLONGE_USERNAME


def get_or_fetch_challonge_tourney_info_file_from_parts(
        organisation_name: Optional[str], tourney_id_to_fetch: str) -> Optional[dict]:
    """
    Get or fetch the specified tournament's information file given by the
    organisation name (optional if not a subdomain) and its tourney id.
    :param organisation_name: The organisation name that hosts this tournament, e.g. "inkleagues"
    :param tourney_id_to_fetch: The tournament name, e.g. "SXD8"
    :return: The tournament information json
    """
    return get_or_fetch_challonge_tourney_info_file_combined(organisation_name + '-' + tourney_id_to_fetch)


def get_or_fetch_challonge_tourney_info_file_combined(
        combined_tourney_name_to_fetch: str) -> Optional[dict]:
    """
    Get or fetch the specified tournament's information file given by the fully-qualified tournament name.
    :param combined_tourney_name_to_fetch: The organisation name and its tournament id, e.g. "inkleagues-SXD8"
    :return: The tournament information json
    """

    if not exists(TOURNEY_INFO_SAVE_DIR):
        makedirs(TOURNEY_INFO_SAVE_DIR)

    filename: str = f'{combined_tourney_name_to_fetch}.json'
    matched_tourney_files = glob.glob(join(TOURNEY_INFO_SAVE_DIR, f'*{filename}'))
    full_path = matched_tourney_files[0] if len(matched_tourney_files) else join(TOURNEY_INFO_SAVE_DIR, filename)
    if not isfile(full_path):
        tourney_contents = challonge.tournaments.show(combined_tourney_name_to_fetch)
        print(tourney_contents)
        if isinstance(tourney_contents, str):
            tourney_contents = json.loads(tourney_contents)

        if len(tourney_contents) == 0:
            print(f'ERROR get_or_fetch_challonge_tourney_info_file_combined: Nothing exists at {combined_tourney_name_to_fetch=}.')
            return None

        if isinstance(tourney_contents, list):
            tourney_contents = tourney_contents[0]

        # Handle tournament contents...
        if 'id' in tourney_contents and 'name' in tourney_contents and 'started_at' in tourney_contents:
            tourney_name = tourney_contents["name"].replace(" ", "-")
            start_time: datetime = tourney_contents['started_at']
            filename = f'{start_time.strftime("%Y-%m-%d")}-{tourney_name}-{combined_tourney_name_to_fetch}.json'
            full_path = join(TOURNEY_INFO_SAVE_DIR, filename)
            save_as_json_to_file(full_path, tourney_contents)
            print(f'OK! (Saved read tourney info file to {full_path})')

            # Retrieve the participants for a given tournament.
            team_contents = challonge.participants.index(tourney_contents["id"])

            if isinstance(team_contents, str):
                team_contents = json.loads(team_contents)

            full_path = join(TOURNEY_TEAMS_SAVE_DIR, filename)
            save_as_json_to_file(full_path, team_contents)
            print(f'OK! (Saved read teams file to {full_path})')

            parent_dir = join(STAGES_SAVE_DIR, combined_tourney_name_to_fetch)
            makedirs(parent_dir)
            full_path = join(parent_dir, filename)
            save_as_json_to_file(full_path, challonge.matches.index(tourney_contents["id"]))
            print(f'OK! (Saved read stages results file to {full_path})')

        else:
            print(f"Couldn't name the downloaded tourney info file. Not using: "
                  f"{'id' in tourney_contents=} "
                  f"{'name' in tourney_contents=} "
                  f"{'started_at' in tourney_contents=}")

    else:
        tourney_contents = load_json_from_file(full_path)

        if isinstance(tourney_contents, list):
            tourney_contents = tourney_contents[0]
    return tourney_contents


if __name__ == '__main__':
    challonge.set_credentials(CHALLONGE_USERNAME, CHALLONGE_API_KEY)

    for global_id_to_fetch in [input('id/url? NOTE FOR SUBDOMAINS YOU MUST PREPEND THE SUBDOMAIN TO THE ID e.g. paddling-abc123')]:
        get_or_fetch_challonge_tourney_info_file_combined(global_id_to_fetch)
