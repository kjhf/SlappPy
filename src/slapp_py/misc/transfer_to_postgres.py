import json
import os
from os.path import isfile

import dotenv
import psycopg2
from battlefy_toolkit.caching.fileio import load_json_from_file

from slapp_py.misc.create_tables import create_tables

if __name__ == '__main__':
    dotenv.load_dotenv()

    connection = None
    cursor = None

    try:
        connection = psycopg2.connect(
            host=os.getenv("DATABASE_HOST"),
            database=os.getenv("DATABASE_NAME"),
            user=os.getenv("DATABASE_USER"),
            password=os.getenv("DATABASE_PASSWORD"))

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
            for i, p in enumerate(players_snapshot):
                this_id = p['Id']
                this_names = p['Names']
                this_teams = p['Teams']
                this_sources = p['Sources']
                this_discord_name = p['DiscordName']
                this_friend_code = p['FriendCode']

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
            for i, t in enumerate(teams_snapshot):
                this_id = t['Id']
                this_name = t['Name']
                this_div = json.dumps(t['Div'])
                this_clan_tags = t['ClanTags']
                this_clan_tag_option = t['ClanTagOption']
                # SQL uses index 1 for enums
                cursor.execute(f'SELECT (ENUM_RANGE(NULL::clan_tag_option_enum))[{this_clan_tag_option + 1}]'
                               f'FROM generate_series(1, 5) s')
                # This returns the result in array of length 5. Just get the first to squash.
                this_clan_tag_option = cursor.fetchall()[0]
                this_sources = t['Sources']
                this_twitter = t['Twitter']

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
