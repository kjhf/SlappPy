import json
from typing import List

import requests
from bs4 import BeautifulSoup

from util.utils import fetch_address, save_to_file

TOONAMENT_ADDRESS_FORMAT: str = 'https://www.toornament.com/en_GB/tournaments/%s'
TEAMS_ADDRESS_FORMAT: str = 'https://www.toornament.com/en_GB/tournaments/%s/participants/'

# Ids: https://www.toornament.com/en_GB/playlists/2543959016689573888
# Stages: https://www.toornament.com/en_GB/tournaments/3539133076478918656/stages/3550924671560138752/
# Teams (participants): view-source:https://www.toornament.com/en_GB/tournaments/3539133076478918656/participants/

if __name__ == '__main__':
    id_to_fetch = input('id?')
    address = TOONAMENT_ADDRESS_FORMAT % id_to_fetch
    print(f'Getting tourney from {address}')

    response = requests.get(address)
    assert response.status_code == 200

    # Parse HTML
    # https://www.digitalocean.com/community/tutorials/how-to-scrape-web-pages-with-beautiful-soup-and-python-3
    soup = BeautifulSoup(response.text, 'html.parser')
    division_parent_attrs = {'class': 'structure-group'}
    title_attrs = {'class': 'title'}
    rank_attrs = {'class': 'rank'}
    name_attrs = {'class': 'name'}
    division_elements = soup.find_all('div', attrs=division_parent_attrs)
    found_teams: List[dict] = []

    # view-source:https://www.toornament.com/en_GB/tournaments/3539133076478918656/stages/3550924671560138752/
    for div_el in division_elements:
        division = div_el.find('div', attrs=title_attrs)
        rank = div_el.find('div', attrs=rank_attrs)
        name = div_el.find('div', attrs=name_attrs)
        team = {
            "Div":
                {
                    "DivType": 2,
                    "Value": division
                },
            "Name": name,
            "Sources": [f"Toonament-{id_to_fetch}"]
        }
        found_teams.append(team)

    # Now get the players for the teams
    response = fetch_address(TEAMS_ADDRESS_FORMAT % id_to_fetch)
    save_to_file(f'{id_to_fetch}.json', json.dumps(found_teams))
