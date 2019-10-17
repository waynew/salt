# -*- coding: utf-8 -
"""
Simple helper for creating cards in a GitHub Project board.
"""

import argparse
import getpass

import requests
from argparse import Namespace
from pathlib import Path
from typing import List, Tuple

NEED_BACKPORT_COLUMN = "6831403"
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
    for pr in prs_to_post:
        url = f"https://api.github.com/repos/{OWNER_REPO}/pulls/{pr}"
        r = requests.get(
            url,
            auth=auth,
            headers={"Accept": "application/vnd.github.inertia-preview+json"},
        )
        id = r.json()["id"]
        url = f"https://api.github.com/projects/columns/{NEED_BACKPORT_COLUMN}/cards"
        r = requests.post(
            url,
            auth=auth,
            headers={"Accept": "application/vnd.github.inertia-preview+json"},
            json={"content_id": id, "content_type": "PullRequest"},
        )
        print("Created card for ", pr)


if __name__ == "__main__":
    args: Namespace = parser.parse_args()
    make_the_issues(
        pr_list=args.PR_LIST_FILE.read().splitlines(),
        auth=(args.github_api_user, args.github_api_token.read().strip()),
    )
