import datetime
import json
from os.path import isfile

from SlapPy.backtrace_discord_id import backtrace_discord_id, clear_reset_time

if __name__ == '__main__':
    # The dump file is a partial download that contains a dump of responses bytes on each line, e.g.
    # b'{"id": "1122334455", "username": "MyUser", "avatar": "he57121", "discriminator": "1234", "public_flags": 0}'
    dump_path: str = input('Dump file? (Enter to skip)').replace('"', '')
    dump = {}
    if len(dump_path) > 0:
        assert isfile(dump_path)
        print('✔ Is a file.')
        with open(dump_path, 'r', encoding='utf-8') as infile:
            for line in infile.readlines():
                value = (json.loads(eval(line)))
                discord_id = value['id']
                dump[discord_id] = value

    # The Sendou file is the json response containing registered users.
    # The magic happens by marrying the discord_id with the current information.
    sendou_path: str = input('Sendou file? (Enter to skip)').replace('"', '')
    if len(sendou_path) > 0:
        assert isfile(sendou_path)
        print('✔ Is a file.')
        with open(sendou_path, 'r', encoding='utf-8') as infile:
            players_snapshot = json.load(infile)["data"]

        users_node = players_snapshot["users"]
        print(f'Processing {len(users_node)} players.')
        last_time = datetime.datetime.now()
        for i in users_node:
            if 'discord_id' in i:
                discord_id = i["discord_id"]
                if discord_id in dump:
                    i["discord"] = dump[discord_id]
                    del i["discord_id"]
                else:
                    try:
                        response = backtrace_discord_id(discord_id)
                        i["discord"] = response
                        del i["discord_id"]
                    except KeyboardInterrupt:
                        input("Interrupt received, enter to continue...")
                        clear_reset_time()
        print("Done.")
        print(players_snapshot)

        with open(sendou_path, 'w', encoding='utf-8') as outfile:
            json.dump(players_snapshot, outfile)
