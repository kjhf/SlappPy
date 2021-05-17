import json
from os.path import isfile

import psycopg2
from caching.fileio import load_json_from_file  # battlefy-toolkit

from misc.create_tables import create_tables
from tokens import *

if __name__ == '__main__':
    connection = None
    cursor = None

    try:
        connection = psycopg2.connect(
            host=HOST,
            database=DATABASE,
            user=USER,
            password=PASSWORD)

        # Create a cursor
        cursor = connection.cursor()

        # Cool, we're connected, let's transfer.
        # Create tables
        print(f'Creating Tables')
        create_tables(cursor)

        players_snapshot_path: str = input('Players snapshot file? (Enter to skip)').replace('"', '')
        if len(players_snapshot_path) > 0:
            assert isfile(players_snapshot_path)
            print('✔ Is a file.')
            players_snapshot = load_json_from_file(players_snapshot_path)

            print(f'Processing {len(players_snapshot)} players.')
            for i, _ in enumerate(players_snapshot):
                this_id = players_snapshot[i]['Id']
                this_names = players_snapshot[i]['Names']
                this_teams = players_snapshot[i]['Teams']
                this_sources = players_snapshot[i]['Sources']
                this_discord_name = players_snapshot[i]['DiscordName']
                this_friend_code = players_snapshot[i]['FriendCode']

                execute_str = "INSERT INTO players (id, names, teams, sources, discord_name, friend_code) " \
                              "VALUES (%s, %s, %s, %s, %s, %s);"
                cursor.execute(
                    execute_str,
                    (this_id, this_names, this_teams, this_sources, this_discord_name, this_friend_code,)
                )
                # Use fetch all to get returned data.
                # Raises "psycopg2.ProgrammingError: no results to fetch" for insertions.
                # returned_data = cursor.fetchall()

            print("Committing...")
            connection.commit()

        teams_snapshot_path: str = input('Teams snapshot file? (Enter to skip)').replace('"', '')
        if len(teams_snapshot_path) > 0:
            assert isfile(teams_snapshot_path)
            print('✔ Is a file.')
            teams_snapshot = load_json_from_file(teams_snapshot_path)

            print(f'Loaded {len(teams_snapshot)} teams.')
            for i, _ in enumerate(teams_snapshot):
                this_id = teams_snapshot[i]['Id']
                this_name = teams_snapshot[i]['Name']
                this_div = json.dumps(teams_snapshot[i]['Div'])
                this_clan_tags = teams_snapshot[i]['ClanTags']
                this_clan_tag_option = teams_snapshot[i]['ClanTagOption']
                # SQL uses index 1 for enums
                cursor.execute(f'SELECT (ENUM_RANGE(NULL::clan_tag_option_enum))[{this_clan_tag_option + 1}]'
                               f'FROM generate_series(1, 5) s')
                # This returns the result in array of length 5. Just get the first to squash.
                this_clan_tag_option = cursor.fetchall()[0]
                this_sources = teams_snapshot[i]['Sources']
                this_twitter = teams_snapshot[i]['Twitter']

                execute_str = "INSERT INTO teams (id, name, div, clan_tags, clan_tag_option, sources, twitter) " \
                              "VALUES (%s, %s, %s, %s, %s, %s, %s);"
                cursor.execute(
                    execute_str,
                    (this_id, this_name, this_div, this_clan_tags, this_clan_tag_option, this_sources, this_twitter, )
                )
            print("Committing...")
            connection.commit()

        # close the communication with the PostgreSQL
        print("Closing...")
        cursor.close()
        cursor = None
        connection.close()
        connection = None
    except (Exception, psycopg2.DatabaseError) as error:
        print("Except...")
        print(error)
        raise error
    finally:
        print("Finally...")
        if cursor is not None:
            cursor.close()
            print('Cursor closed.')

        if connection is not None:
            connection.close()
            print('Connection closed.')
