import glob
import os
import sys
from os.path import join, exists

from battlefy_toolkit.caching.fileio import load_json_from_file
from dateutil.parser import isoparse

from slapp_py.misc.slapp_files_utils import TOURNEY_TEAMS_SAVE_DIR, TOURNEY_INFO_SAVE_DIR, STAGES_SAVE_DIR
from tokens import SLAPP_APP_DATA


def conditional_move(_src, _dest) -> bool:
    do_move = _src != _dest
    if do_move:
        os.rename(_src, _dest)
        print(f"conditional_move: {_src} -> {_dest}")
    return do_move


if __name__ == '__main__':
    # For each file in local, sort into the correct folder.
    work_dir = input('Work directory?')
    if not os.path.isdir(work_dir):
        print('Directory not found.')
        sys.exit(1)

    files_list = glob.glob(join(work_dir, "*.json"), recursive=True)

    for file_path in files_list:
        if not os.path.isfile(file_path):
            continue

        file_path = os.path.abspath(file_path)
        file = os.path.basename(file_path)
        parent_dir = os.path.abspath(os.path.join(file_path, os.pardir))

        if parent_dir.rstrip(os.path.sep).endswith(os.path.sep + 'old'):
            continue

        if parent_dir.rstrip(os.path.sep).endswith(os.path.sep + 'statink'):
            continue

        if file.startswith("Snapshot-"):
            destination_path = join(SLAPP_APP_DATA, file)
            if file_path != destination_path:
                os.rename(file_path, destination_path)
                continue

        json_contents = load_json_from_file(file_path)

        if json_contents and isinstance(json_contents, list):
            json_contents = json_contents[0]

        if '_id' in json_contents and \
                'userID' in json_contents and \
                'customFields' in json_contents:
            # This is a tourney teams file.
            if not exists(TOURNEY_TEAMS_SAVE_DIR):
                os.makedirs(TOURNEY_TEAMS_SAVE_DIR)
            destination_path = join(TOURNEY_TEAMS_SAVE_DIR, file)
            if conditional_move(file_path, destination_path):
                continue

        elif '_id' in json_contents and \
                'rules' in json_contents:
            # This is a tourney info file.
            if not exists(TOURNEY_INFO_SAVE_DIR):
                os.makedirs(TOURNEY_INFO_SAVE_DIR)

            if '_id' in json_contents and 'slug' in json_contents and 'startTime' in json_contents:
                start_time = isoparse(json_contents['startTime'])
                filename = f'{start_time.strftime("%Y-%m-%d")}-{json_contents["slug"]}-' \
                           f'{json_contents["_id"]}.json'
                destination_path = join(TOURNEY_INFO_SAVE_DIR, filename)
            else:
                print(f"Couldn't name the downloaded file: "
                      f"{'_id' in json_contents=} "
                      f"{'slug' in json_contents=} "
                      f"{'startTime' in json_contents=}")
                destination_path = join(TOURNEY_INFO_SAVE_DIR, file)

            conditional_move(file_path, destination_path)
            if conditional_move(file_path, destination_path):
                continue

        elif '_id' in json_contents and \
                'bracket' in json_contents and \
                'standingIDs' in json_contents and \
                'matches' in json_contents:
            # This is a tourney stage (battlefy) file.
            tournamentID = json_contents["matches"].get("top", {}).get("tournamentID", "__UNKNOWN")
            destination_folder = join(STAGES_SAVE_DIR, tournamentID)
            if not exists(destination_folder):
                os.makedirs(destination_folder)
            destination_path = join(destination_folder, file)
            if conditional_move(file_path, destination_path):
                continue

        elif '_id' in json_contents and \
                'stageID' in json_contents and \
                'opponents' in json_contents and \
                'team' in json_contents:
            # This is a tourney stage (standings) file.
            tournamentID = json_contents["team"].get("tournamentID", "__UNKNOWN")
            destination_folder = join(STAGES_SAVE_DIR, tournamentID)
            if not exists(destination_folder):
                os.makedirs(destination_folder)
            destination_path = join(destination_folder, file)
            if conditional_move(file_path, destination_path):
                continue

        else:
            print("Don't know what this is, skipping: " + file_path)
