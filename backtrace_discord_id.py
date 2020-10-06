import requests

from SlapPy.tokens import BOT_TOKEN


def backtrace_discord_id(discord_id: int):
    url = 'https://discord.com/api/users/' + discord_id.__str__()
    headers = {'Authorization': 'Bot ' + BOT_TOKEN}
    response = requests.get(url, headers=headers)
    print(response)
    print(response.content)
    return response.content


if __name__ == '__main__':
    backtrace_discord_id(97288493029416960)
