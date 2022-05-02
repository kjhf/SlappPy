import csv
from datetime import datetime

import dotenv
import logging
from battlefy_toolkit.caching.fileio import load_json_from_file
from slapp_py.helpers.console_helper import ask, pause
from slapp_py.misc.download_from_battlefy_result import get_or_fetch_tourney_information
from slapp_py.misc.models.tournament_information import TournamentInformation
from slapp_py.sources_builder.source_file_builder import fetch_tournament_ids, generate_new_sources_files, patch_sources, \
    rebuild_sources, update_sources_with_placements
from slapp_py.sources_builder.sources_to_skills import update_sources_with_skills


def full_rebuild(skip_pauses: bool = False, patch: bool = True):
    # Plan of attack:
    # 1. Get all the tourney ids
    # 2. Update the sources.yaml list
    # 3. Rebuild or patch the database
    # 4. Add in placements     -- again, if we keep what's already there, we'd only be adding to new tourneys
    # 5. Calculate ELO         -- again, calculating only the new bits

    # Phase 1. Tourney ids
    do_fetch_tourney_ids = ask("Fetch new tourney ids? [Y/N]")
    if do_fetch_tourney_ids:
        full_tourney_ids = fetch_tournament_ids("Phase 1 Ids.json")
        print(f"Phase 1 done, {len(full_tourney_ids)} ids saved.")
    else:
        print(f"Phase 1 loading from file...")
        full_tourney_ids = load_json_from_file("Phase 1 Ids.json")

    # Phase 1.5 - Translate tournaments into information for us to use internally
    tournament_information = [get_or_fetch_tourney_information(tournament_id) for tournament_id in full_tourney_ids]
    with open(f"{datetime.strftime(datetime.now(), '%Y-%m-%d-%H-%M-%S')}-tournament-information.csv", 'w', encoding='UTF8') as f:
        writer = csv.writer(f)
        writer.writerow(TournamentInformation.get_headers())
        for info in tournament_information:
            writer.writerow(info.to_row())

    # Phase 2. Updates sources list
    new_sources_file_path, patch_sources_file_path = generate_new_sources_files(full_tourney_ids, skip_redownload=True)
    print("Phase 2 done.")

    # Phase 3. Rebuild/patch/skip
    option = "1" if patch else "2"
    if not skip_pauses:
        option = input(
            "Select an option:\n"
            "1. Patch current\n"
            "2. Rebuild\n"
            "(other). Skip\n")

    if option == "1":
        patch_sources(patch_sources_file_path)

    elif option == "2":
        rebuild_sources(new_sources_file_path)

    print("Phase 3 done.")

    # Phase 4. Add in the placements
    if not skip_pauses:
        pause(True)
    update_sources_with_placements()

    print("Phase 4 done.")
    # Phase 5. Calculate ELO
    if not skip_pauses:
        pause(True)
    update_sources_with_skills(clear_current_skills=True)
    print("Phase 5 done, complete!")


if __name__ == '__main__':
    dotenv.load_dotenv()
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger().setLevel("DEBUG")

    full_rebuild(skip_pauses=True, patch=False)
    # update_sources_with_placements()
    # update_sources_with_skills(clear_current_skills=True)
    pass
