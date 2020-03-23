import argparse
import logging
import pathlib
import subprocess

import quiz

GITHUB_GRAPHQL_API = "https://api.github.com/graphql"


log = logging.getLogger(__name__)


def make_parser():
    parser = argparse.ArgumentParser("commits-in-pr.py")
    parser.add_argument("pr_number", type=int, help="Pull Request number, e.g. 12345")
    parser.add_argument("--owner", default="saltstack", help="Repo owner")
    parser.add_argument("--reponame", default="salt", help="Repo name")
    parser.add_argument("--github-api-user", help="GitHub API username")
    parser.add_argument("--github-api-token", help="GitHub API token")
    parser.add_argument(
        "--oneline", action="store_true", help="Print git commit hashes on one line"
    )
    parser.add_argument("--exclude-merge-commits", type=bool, default=True, help="Exclude merge commits.")
    return parser


def get_schema(*, auth, url):
    schema_path = (
        pathlib.Path(__file__).parent / ".cache/github_schema.json"
    ).resolve()
    schema_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        log.debug("Loading schema from file...")
        schema = quiz.Schema.from_path(schema_path)
        log.debug("Done!")
    except FileNotFoundError:
        log.debug(f"Failed - fallback to load from {url}")
        debug("Loading...")
        schema = quiz.Schema.from_url(url, auth=auth)
        schema.to_path(schema_path)
        debug("Done!")
    return schema


def load_auth():
    token_path = pathlib.Path("~/.gittoken").expanduser()
    user, token = token_path.read_text().strip().split()
    return (user, token)


def do_it(*, owner, reponame, pr_number, auth, oneline, exclude_merge_commits):  # Shia LeBeouf
    auth = load_auth()
    schema = get_schema(auth=auth, url=GITHUB_GRAPHQL_API)
    _ = quiz.SELECTOR

    # fmt: off
    query = schema.query[
        _
        .repository(owner=owner, name=reponame)[
            _
            ("pull_request").pullRequest(number=pr_number)[
                _
                .commits(first=100)[
                    _
                    .nodes[
                        _
                        .commit[
                            _
                            .oid
                        ]
                    ]
                ]
            ]
        ]
    ]
    # fmt: on
    result = quiz.execute(query, GITHUB_GRAPHQL_API, auth=auth)
    for node in result.repository.pull_request.commits.nodes:
        if exclude_merge_commits:
            result = subprocess.run(['git', 'show', '-s', '--pretty=%P', node.commit.oid], capture_output=True)
            if len(result.stdout.decode().strip().split()) > 1:
                continue
        print(node.commit.oid, end=" " if oneline else "\n")


if __name__ == "__main__":
    parser = make_parser()
    args = parser.parse_args()
    if args.github_api_user and args.github_api_token:
        auth = (args.github_api_user, args.github_api_token)
    else:
        auth = load_auth()
    do_it(
        owner=args.owner,
        reponame=args.reponame,
        pr_number=args.pr_number,
        auth=auth,
        oneline=args.oneline,
        exclude_merge_commits=args.exclude_merge_commits,
    )
