# -*- coding: utf-8 -
"""
Simple helper for creating cards in a GitHub Project board.
"""

import argparse
import getpass
import sys
from pprint import pprint

import requests
from argparse import Namespace
from pathlib import Path
from typing import List, Tuple, Set

NEED_BACKPORT_COLUMN = "6831403"
NEED_MERGE_COLUMN = "6831406"
OWNER_REPO = "saltstack/salt"

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument(
    "PR_LIST_FILE",
    type=argparse.FileType("r"),
    help="File that contains a list of PR #s to create cards for, one per line.",
)
parser.add_argument(
    "--github-api-token",
    type=argparse.FileType("r"),
    default=Path("~/.gittoken").expanduser().open(),
    help="Path to a file containing only the GitHub API token.",
)
parser.add_argument(
    "--github-api-user",
    default=getpass.getuser(),
    help="GitHub API user - defaults to the current user",
)


def get_existing_pr_numbers(*, auth: Tuple[str, str], column: str) -> Set[int]:
    """

    Args:
        auth: (username, api_token) for GitHub API.
        column: GitHub project column ID.

    Returns:
        set of existing PR numbers gleaned from the cards in the column.

    """
    url = f"https://api.github.com/projects/columns/{column}/cards"
    has_next = True
    existing_numbers = set()
    col = "content_url"
    while has_next:
        print("getting", url)
        r = requests.get(
            url,
            auth=auth,
            headers={"Accept": "application/vnd.github.inertia-preview+json"},
        )

        existing_numbers.update(
            int(card[col].rpartition("/")[-1]) for card in r.json() if col in card
        )

        if "next" in r.links:
            url = r.links["next"]["url"]
        else:
            has_next = False

    return existing_numbers


def make_the_issues(pr_list: List[str], auth: Tuple[str, str]) -> None:
    url = f"https://api.github.com/projects/columns/{NEED_BACKPORT_COLUMN}/cards"
    r = requests.head(
        url,
        auth=auth,
        headers={"Accept": "application/vnd.github.inertia-preview+json"},
    )
    last = 1
    try:
        for link in r.headers["Link"].split(","):
            if link.strip().endswith('rel="last"'):
                last = int(link.split("?")[1].split("page=")[1].split(">")[0])
    except KeyError:
        pass
    existing_pr_numbers = []
    for page in range(last):
        r = requests.get(
            url,
            params={"page": page + 1},
            auth=auth,
            headers={"Accept": "application/vnd.github.inertia-preview+json"},
        )
        col = "content_url"
        existing_pr_numbers.extend(
            card[col].rpartition("/")[-1] for card in r.json() if col in card
        )
    prs_to_post = set(pr_list) - set(existing_pr_numbers)
    for pr in sorted(prs_to_post):
        id = get_pr_id(auth=auth, pr_number=pr)
        url = f"https://api.github.com/projects/columns/{NEED_BACKPORT_COLUMN}/cards"
        r = requests.post(
            url,
            auth=auth,
            headers={"Accept": "application/vnd.github.inertia-preview+json"},
            json={"content_id": id, "content_type": "PullRequest"},
        )
        print("Created card for ", pr)


def create_needs_pr_card(auth, pr_id):
    url = f"https://api.github.com/projects/columns/{NEED_MERGE_COLUMN}/cards"
    print(f"ID {type(pr_id)} {pr_id!r}")
    r = requests.post(
        url=url,
        auth=auth,
        headers={"Accept": "application/vnd.github.inertia-preview+json"},
        json={"content_id": pr_id, "content_type": "PullRequest"},
    )
    if r.status_code != 201:
        data = r.json()
        print(data)
        if 'Project already has the associated issue' not in str(data):
            sys.exit(r.status_code)


def get_pr_id(auth, pr_number):
    url = f"https://api.github.com/repos/{OWNER_REPO}/pulls/{pr_number}"
    r = requests.get(
        url,
        auth=auth,
        headers={"Accept": "application/vnd.github.inertia-preview+json"},
    )
    id = r.json()["id"]
    return id


def create_needs_prs(auth):
    existing_numbers = get_existing_pr_numbers(auth=auth, column=NEED_MERGE_COLUMN)
    url = f"https://api.github.com/repos/{OWNER_REPO}/issues"
    has_next = True
    while has_next:
        r = requests.get(url, auth=auth, params={"labels": "master-port", "state": "all"})

        for pr in r.json():
            if pr["number"] in existing_numbers:
                # Already exists? No need to create!
                continue
            pr_id = get_pr_id(auth, pr["number"])
            print("Creating card for", pr["number"], pr["id"], pr_id)
            create_needs_pr_card(auth=auth, pr_id=pr_id)

        if "next" in r.links:
            url = r.links["next"]["url"]
        else:
            has_next = False


if __name__ == "__main__":
    args: Namespace = parser.parse_args()
    auth = (args.github_api_user, args.github_api_token.read().strip())
    make_the_issues(
       pr_list=args.PR_LIST_FILE.read().splitlines(),
       auth=auth,
    )
    #create_needs_prs(auth=auth)
