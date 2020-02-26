import pprint
import requests
from pathlib import Path


def list_all_the_prs(auth):
    url = "https://api.github.com/repos/saltstack/salt/pulls?per_page=100"
    has_next = True
    derp = Path("~/blarp/").expanduser()
    derp.mkdir(exist_ok=True, parents=True)
    while has_next:
        r = requests.get(url)
        url = r.links.get("next", {}).get("url")
        if url is None:
            has_next = False
        for pull in r.json():
            if "waynew" in (r["login"] for r in pull["requested_reviewers"]):
                pr = pull["number"]
                print(pr)

                p = requests.get(
                    f"https://api.github.com/repos/saltstack/salt/pulls/{pr}/files",
                    auth=auth,
                ).json()
                has_any_tests = False
                for change in p:
                    if "filename" in change and change["filename"].startswith("tests/"):
                        has_any_tests = True

                thing = derp / f"{pr}.txt"
                thing.write_text(
                    f"URL: {pull['html_url']}\nHas-Any-Tests: {has_any_tests}\n"
                )


gh_token = Path("~/.gittoken").expanduser().read_text().strip()
auth = ("waynew", gh_token)
list_all_the_prs(auth)
exit()
results = requests.get(
    "https://api.github.com/search/issues?q=is:pr+is:open+review-requested:waynew+sort:created-asc+repo:saltstack/salt&per_page=100",
    headers={"Accept": "application/vnd.github.v3+json"},
    auth=auth,
).json()

derp = Path("~/blarp/").expanduser()
derp.mkdir(exist_ok=True, parents=True)

size = len(results["items"])
for i, item in enumerate(results["items"], start=1):
    print(f"{i}/{size}", end="\r")
    url = item["pull_request"]["url"]

    r = requests.get(url, auth=auth).json()

    pr = r["number"]

    p = requests.get(
        f"https://api.github.com/repos/saltstack/salt/pulls/{pr}/files", auth=auth
    ).json()

    has_any_tests = False
    for change in p:
        if "filename" in change and change["filename"].startswith("tests/"):
            has_any_tests = True

    thing = derp / f"{pr}.txt"
    thing.write_text(f"URL: {r['html_url']}\nHas-Any-Tests: {has_any_tests}\n")
