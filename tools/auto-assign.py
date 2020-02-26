import requests
import sys

from itertools import cycle
from pathlib import Path
from pprint import pprint


USERS = [
    "Ch3LL",
    "garethgreenaway",
    "Akm0d",
    "dhiltonp",
    "s0undt3ch",
    "DmitryKuzmenko",
    "xeacott",
    "dwoz",
    "waynew",
]


def get_the_issues(auth):
    r = requests.get(
        "https://api.github.com/search/issues?q=label:master-port+no:assignee+state:open&per_page=100"
    )
    return r.json()["items"]


def assign_le_issues(issues):
    for issue, person in zip(issues, cycle(USERS)):
        issue_num = issue["number"]
        print(f'Assigning {issue["number"]} to {person}...', end="")
        sys.stdout.flush()
        r = requests.post(
            f"https://api.github.com/repos/saltstack/salt/issues/{issue_num}/assignees",
            auth=auth,
            json={"assignees": [person]},
        )
        data = r.json()
        if r.status_code == 201:
            print("OK!", data["html_url"])
        else:
            print("Fail", data)


if __name__ == "__main__":
    with Path("~/.gittoken").expanduser().open() as f:
        auth = ("waynew", f.read().strip())

    issues = get_the_issues(auth)
    while issues:
        assign_le_issues(issues)
        issues = get_the_issues(auth)
