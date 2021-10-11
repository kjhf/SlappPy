import asyncio
import glob
import json
import logging
import sys
from os.path import join, relpath
from typing import Set, Dict, Tuple, Collection

import dotenv
from battlefy_toolkit.caching.fileio import load_json_from_file, save_as_json_to_file, save_text_to_file
from battlefy_toolkit.downloaders.tourney_downloader import get_or_fetch_tourney_ids

from slapp_py.helpers.str_helper import equals_ignore_case, is_none_or_whitespace
from slapp_py.misc.download_from_battlefy_result import get_or_fetch_tourney_teams_file, \
    update_sources_with_placements
from slapp_py.misc.slapp_files_utils import TOURNEY_TEAMS_SAVE_DIR
from slapp_py.misc.sources_to_skills import update_sources_with_skills
from slapp_py.slapp_runner.slapipes import initialise_slapp, SLAPP_DATA_FOLDER


async def receive_slapp_response(success_message: str, response: dict):
    print("Success: " + success_message + ", dict: " + json.dumps(response))


def ask(question: str):
    while True:
        answer = input(question)
        if equals_ignore_case('y', answer) or equals_ignore_case('yes', answer) or equals_ignore_case('true', answer):
            return True
        elif equals_ignore_case('n', answer) or equals_ignore_case('no', answer) or equals_ignore_case('false', answer):
            return False


def pause(exit_if_no: bool = False):
    do_continue = True
    while do_continue:
        continue_str = 'Continue? [y/n]' if exit_if_no else 'Press enter to continue.'
        answer = input("Paused. " + continue_str)
        if exit_if_no:
            if equals_ignore_case('y', answer) or equals_ignore_case('yes', answer):
                break
            elif equals_ignore_case('n', answer) or equals_ignore_case('no', answer):
                sys.exit(0)
        else:
            break


def _phase_1() -> Set[str]:
    print("Fetching tourney ids...")
    full_tourney_ids = get_or_fetch_tourney_ids()

    print(f"Getting tourneys from the ids ({len(full_tourney_ids)} to get)")
    for tourney_id in full_tourney_ids:
        get_or_fetch_tourney_teams_file(tourney_id)

    print("Saving...")
    save_as_json_to_file("Phase 1 Ids.json", list(full_tourney_ids))
    return full_tourney_ids


def _phase_2(battlefy_ids: Collection) -> Tuple[str, str]:
    # Current sources:
    sources_contents = _load_sources_file()
    print(f"{len(sources_contents)} sources loaded from current sources yaml. {len(battlefy_ids)} Battlefy Ids known. (Diff of {len(battlefy_ids) - len(sources_contents)}).")

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
                    relative_path = '.\\' + relative_path
                processed_tourney_ids[tourney_id] = (relative_path, True)
            else:
                print(f"ERROR: Found an updated tourney file but a unique file wasn't downloaded for it: "
                      f"{tourney_id=}, {len(matched_tourney_teams_files)=}")
                print("Re-attempting download...")
                if get_or_fetch_tourney_teams_file(tourney_id):
                    print("Success!")
                    matched_tourney_teams_files = glob.glob(join(TOURNEY_TEAMS_SAVE_DIR, f'*{filename}'))
                    if len(matched_tourney_teams_files) == 1:
                        relative_path = relpath(matched_tourney_teams_files[0], start=SLAPP_DATA_FOLDER)
                        processed_tourney_ids[tourney_id] = (relative_path, True)
                    else:
                        print(f"ERROR: Reattempt failed. Please debug."
                              f"{tourney_id=}, {len(matched_tourney_teams_files)=}")
                else:
                    print(f"ERROR: Reattempt failed. Skipping file."
                          f"{tourney_id=}, {len(matched_tourney_teams_files)=}")

    # Now update the yaml
    print(f"Updating the yaml ({len(sources_contents)} sources).")
    # Take care of those pesky exceptions to the rule

    # Sendou goes first (but only if not dated)
    # If dated, it's special and should be added back in
    if 'Sendou.json' in sources_contents[0]:
        sendou_str = sources_contents[0]
        sources_contents.remove(sources_contents[0])
    else:
        sendou_str = None

    # statink folder is special
    if './statink' in sources_contents:
        statink_present = True
        sources_contents.remove('./statink')
    else:
        statink_present = False

    # Twitter goes last (but only if not dated)
    if 'Twitter.json' in sources_contents[-1]:
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

    # To the start
    if sendou_str:
        sources_contents.insert(0, sendou_str)

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

    print(f"Phase 2 done. {len(sources_contents)} sources written with {len(processed_tourney_ids)} processed ids, "
          f"of which {len(patch_sources_contents)} are new.")
    return new_sources_file_path, patch_sources_file_path


def _phase_3(new_sources_file_path: str, option: str):
    loop = asyncio.get_event_loop()
    command = f"--{option} {new_sources_file_path}"
    print("Calling " + command)

    loop.run_until_complete(
        asyncio.gather(
            initialise_slapp(receive_slapp_response, command)
        )
    )


def _load_sources_file(path: str = join(SLAPP_DATA_FOLDER, 'sources.yaml')):
    with open(path, 'r', encoding='utf-8') as infile:
        return infile.read().split('\n')


def full_rebuild(skip_pauses: bool = False, patch: bool = True):
    # Plan of attack:
    # 1. Get all the tourney ids
    # 2. Update the sources.yaml list
    # 3. Rebuild or patch the database
    # 4. Add in placements     -- again, if we keep what's already there, we'd only be adding to new tourneys
    # 5. Calculate ELO         -- again, calculating only the new bits

    # 1. Tourney ids
    do_fetch_tourney_ids = ask("Fetch new tourney ids? [Y/N]")
    if do_fetch_tourney_ids:
        full_tourney_ids = _phase_1()
        print(f"Phase 1 done, {len(full_tourney_ids)} ids saved.")
    else:
        full_tourney_ids = load_json_from_file("Phase 1 Ids.json")

    # 2. Updates sources list
    new_sources_file_path, patch_sources_file_path = _phase_2(full_tourney_ids)

    # 3. Rebuild or patch
    option = "1" if patch else "2"
    if not skip_pauses:
        option = input(
            "Select an option:\n"
            "1. Patch current\n"
            "2. Rebuild\n"
            "(other). Skip\n")

    if option == "1":
        _phase_3(patch_sources_file_path, "patch")

    elif option == "2":
        _phase_3(new_sources_file_path, "rebuild")

    print("Phase 3 done.")
    # 4. Add in the placements
    if not skip_pauses:
        pause(True)
    update_sources_with_placements()

    print("Phase 4 done.")
    # 5. Calculate ELO
    if not skip_pauses:
        pause(True)
    update_sources_with_skills(clear_current_skills=True)

    print("Phase 5 done, complete!")


if __name__ == '__main__':
    dotenv.load_dotenv()
    logging.basicConfig(level=logging.DEBUG)

    # _phase_3(join(SLAPP_DATA_FOLDER, 'sources_patch.yaml'), "patch")
    update_sources_with_placements()
    update_sources_with_skills(clear_current_skills=True)
    # full_rebuild(skip_pauses=True, patch=False)
