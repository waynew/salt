import json
import sys
import pathlib
import requests
import git.util


CACHE_PATH = pathlib.Path(".cache/pull-assigner.json")


class Reviewer:
    def __init__(self, name):
        self.name = name
        self.prs = []

    @property
    def has_capacity(self):
        # Yeah, this could be bool(self.prs) but the magic number could change
        return len(self.prs) < 1


reviewers = {
    r: Reviewer(r)
    for r in (
        "waynew",
        "Ch3LL",
        "dwoz",
        "dmurphy18",
        "garethgreenaway",
        "DmitryKuzmenko",
        "cmcmarrow",
        "twangboy",
        "Akm0d",
        "xeacott",
        "frogunder",
    )
}


def get_requested_reviewers(*, pr_number, auth):
    url = f"{git.util.GITHUB_API}/repos/saltstack/salt/pulls/{pr_number}/requested_reviewers"
    r = requests.get(
        url,
        auth=auth,
        headers={"Accept": "application/vnd.github.inertia-preview+json"},
    )
    users = [u["login"] for u in r.json().get("users", [])]
    teams = [u["name"] for u in r.json().get("teams", [])]
    return {"reviewers": users, "teams": teams}


def load_from_cache():
    try:
        with CACHE_PATH.open("r") as f:
            return json.load(f)
    except:
        return {}


def save_to_cache(prs):
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CACHE_PATH.open("w") as f:
        json.dump(prs, f)


def get_all_open_prs(*, endpoint, auth, force_reload=False):
    has_next = True
    url = f"{endpoint}/search/issues?q=repo:saltstack%2Fsalt+is:pr+is:open+created:<2020-03-01+sort:created-asc"
    prs = load_from_cache()
    if prs and not force_reload:
        return prs
    while has_next:
        print(f"Getting {url}...", end="")
        sys.stdout.flush()
        r = requests.get(
            url,
            auth=auth,
            headers={"Accept": "application/vnd.github.inertia-preview+json"},
        )
        for pr in r.json()["items"]:
            prs[pr["number"]] = {
                "assignees": [a["login"] for a in pr["assignees"]],
                **get_requested_reviewers(pr_number=pr["number"], auth=auth),
            }
        print("OK!")

        if has_next:='next' in r.links:
            url = r.links["next"]["url"]
    save_to_cache(prs)
    return prs


def do_it(*, force_reload=False):  # Shia LeBeouf
    auth = git.util.load_auth()
    prs = get_all_open_prs(
        endpoint=git.util.GITHUB_API, auth=auth, force_reload=force_reload
    )
    for pr_number in prs:
        pr = prs[pr_number]
        for r in pr["reviewers"]:
            try:
                reviewers[r].prs.append(pr)
            except KeyError:
                print(r, "is not a reviewer")

    for name in reviewers:
        reviewer = reviewers[name]
        if reviewer.has_capacity:
            print(reviewer.name, "has capacity")


if __name__ == "__main__":
    do_it(force_reload=False)
