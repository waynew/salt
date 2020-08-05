import json
import sys
import pathlib
import requests
import git.util
import itertools
from collections import defaultdict


CACHE_PATH = pathlib.Path(".cache/changelog-lister.json")
reviewers = itertools.cycle(
    ['wayne', 'chad', 'gareth', 'kirill', 'pedro'],
)


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


def get_ze_frakken_prs(*, endpoint, auth, force_reload=False):
    has_next = True
    url = f"{endpoint}/search/issues?q=repo:saltstack%2Fsalt+is:pr+is:closed+base:master+merged:>2020-02-10+is:merged"
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
            }
        print("OK!")

        if has_next:='next' in r.links:
            url = r.links["next"]["url"]
    save_to_cache(prs)
    return prs


def do_it(*, force_reload=False):  # Shia LeBeouf
    auth = git.util.load_auth()
    prs = get_ze_frakken_prs(
        endpoint=git.util.GITHUB_API, auth=auth, force_reload=force_reload
    )
    by_reviewer = defaultdict(list)
    for reviewer, pr_number in zip(reviewers, sorted(prs)):
        by_reviewer[reviewer].append(pr_number)
        #print(pr_number, reviewer)
    print(len(prs))
    return
    for reviewer in by_reviewer:
        #print(reviewer, len(by_reviewer[reviewer]))
        for pr in by_reviewer[reviewer]:
            print(f'{reviewer}\t{pr}')


if __name__ == "__main__":
    do_it(force_reload=False)
