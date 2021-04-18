import requests
from typing import Optional

headers = {
    "Cache-Control": "no-cache",
    "Pragma": "no-cache"
}


def get_org(org_slug: str) -> Optional[dict]:
    r = requests.get(f'https://dtmwra1jsgyb0.cloudfront.net/organizations?slug={org_slug}&extend%5Badmins%5D=true'
                     f'&extend%5Bmoderators%5D=true&extend%5Bowner%5D=true&extend%5Brunners%5D=true',
                     headers=headers)
    if r.status_code == 200:
        return r.json()
    else:
        return None


def tournament_ids(org_slug) -> Optional[list]:
    org_data = get_org(org_slug)
    if org_data:
        org_id = org_data[0]["_id"]
    else:
        print('Not able to get the Org ' + org_slug)
        return None

    tournaments = []
    page_one_old = requests.get(f"https://search.battlefy.com/tournament/organization/{org_id}/past?page=1&size=10",
                                headers=headers)
    pages = 0
    if page_one_old.status_code == 200:
        page_one_data = page_one_old.json()
        if "total" in page_one_data:
            pages = int(page_one_data["total"] / 10)
            if pages > 0:
                pages = pages+1
            if (page_one_data["total"] % 10) != 0:
                pages = pages+1
        if "tournaments" in page_one_data:
            for items in page_one_data["tournaments"]:
                tournaments.append(items["_id"])
    else:
        print('Bad response from ' + org_slug + ", id " + org_id)
        return None

    for x in range(2, pages):
        page = requests.get(f"https://search.battlefy.com/tournament/organization/{org_id}/past?page={x}&size=10",
                            headers=headers)
        if page.status_code == 200:
            page_data = page.json()
            if "tournaments" in page_data:
                for items in page_data["tournaments"]:
                    tournaments.append(items["_id"])

    return tournaments
