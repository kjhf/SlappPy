import asyncio
import glob
import json
import sys
from os.path import join, relpath
from typing import Set

from helpers.str_helper import equals_ignore_case, is_none_or_whitespace
from misc import utils
from misc.download_from_battlefy_result import get_or_fetch_tourney_ids, get_or_fetch_tourney_teams_file, \
    update_sources_with_placements
from misc.slapp_files_utils import TOURNEY_TEAMS_SAVE_DIR
from misc.sources_to_skills import update_sources_with_skills
from misc.utils import save_text_to_file
from slapp_py.slapipes import initialise_slapp
from tokens import SLAPP_APP_DATA


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
    print("Getting tourney ids...")
    full_tourney_ids = get_or_fetch_tourney_ids()

    for tourney_id in full_tourney_ids:
        get_or_fetch_tourney_teams_file(tourney_id)

    utils.save_as_json_to_file("Phase 1 Ids.json", list(full_tourney_ids))
    return full_tourney_ids


def _phase_3(new_sources_file_path: str):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        asyncio.gather(
            initialise_slapp(receive_slapp_response, "--rebuild " + new_sources_file_path)
        )
    )


def _load_sources_file(path: str = join(SLAPP_APP_DATA, 'sources.yaml')):
    with open(path, 'r', encoding='utf-8') as infile:
        return infile.read().split('\n')


def full_rebuild(skip_pauses: bool = False):
    # Plan of attack:
    # THIS IS A FULL REBUILD and we shouldn't have to do this every time.
    # 1. Get all the tourney ids
    # 2. Update the sources.yaml list
    # 3. Rebuild the database  -- we could implement a partial update using what we have already
    # 4. Add in placements     -- again, if we kep what's already there, we'd only be adding to new tourneys
    # 5. Calculate ELO         -- again, calculating only the new bits

    # 1. Tourney ids
    do_fetch_tourney_ids = ask("Fetch new tourney ids? [Y/N]")
    if do_fetch_tourney_ids:
        full_tourney_ids = _phase_1()
        print("Phase 1 done.")
    else:
        full_tourney_ids = utils.load_json_from_file("Phase 1 Ids.json")

    # 2. Updates sources list
    # Current sources:
    sources_contents = _load_sources_file()

    # Sources now that we've pulled in the tourney files:
    updated_tourney_ids = set()
    updated_tourney_paths = set()
    for tourney_id in full_tourney_ids:
        # Search the sources yaml
        filename = tourney_id + ".json"
        if any([line.endswith(filename) for line in sources_contents]):
            # Not new
            pass
        else:
            matched_tourney_teams_files = glob.glob(join(TOURNEY_TEAMS_SAVE_DIR, f'*{filename}'))
            if len(matched_tourney_teams_files) == 1:
                relative_path = relpath(matched_tourney_teams_files[0], start=SLAPP_APP_DATA)
                if not relative_path.startswith('.'):
                    relative_path = '.\\' + relative_path
                updated_tourney_paths.add(relative_path)
                updated_tourney_ids.add(tourney_id)
            else:
                print(f"ERROR: Found an updated tourney file but a unique file wasn't downloaded for it: "
                      f"{tourney_id=}, {len(matched_tourney_teams_files)=}")
                print("Re-attempting download...")
                if get_or_fetch_tourney_teams_file(tourney_id):
                    print("Success!")
                    matched_tourney_teams_files = glob.glob(join(TOURNEY_TEAMS_SAVE_DIR, f'*{filename}'))
                    if len(matched_tourney_teams_files) == 1:
                        relative_path = relpath(matched_tourney_teams_files[0], start=SLAPP_APP_DATA)
                        updated_tourney_paths.add(relative_path)
                        updated_tourney_ids.add(tourney_id)
                    else:
                        print(f"ERROR: Reattempt failed. Please debug."
                              f"{tourney_id=}, {len(matched_tourney_teams_files)=}")
                else:
                    print(f"ERROR: Reattempt failed. Skipping file."
                          f"{tourney_id=}, {len(matched_tourney_teams_files)=}")

    # Now update the yaml
    # Take care of those pesky exceptions to the rule

    # Sendou goes first (but only if not dated)
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
    for updated_path in updated_tourney_paths:
        sources_contents.append(updated_path)

    # Replace backslashes with forwards
    sources_contents = [line.replace('\\', '/') for line in sources_contents]

    # Sort by order.
    sources_contents.sort()

    # Add the exceptions back in to the correct places
    if sendou_str:
        sources_contents.insert(0, sendou_str)

    if statink_present:
        sources_contents.insert(1, './statink')

    if twitter_str:
        sources_contents.append(twitter_str)

    # Remove blank lines
    sources_contents = list(filter(lambda x: not is_none_or_whitespace(x), sources_contents))

    new_sources_file_path = join(SLAPP_APP_DATA, 'sources_new.yaml')
    save_text_to_file(path=new_sources_file_path,
                      content='\n'.join(sources_contents))

    print(f"Phase 2 done. {updated_tourney_ids=}")

    # 3. Rebuild
    # if yes, call --rebuild [path]
    do_rebuild = True
    if not skip_pauses:
        do_rebuild = ask("Is a rebuild needed?")

    if do_rebuild:
        _phase_3(new_sources_file_path)

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
    _phase_3(join(SLAPP_APP_DATA, 'sources.yaml'))
    update_sources_with_placements()
    update_sources_with_skills(clear_current_skills=True)
