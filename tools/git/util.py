import argparse
import logging
import pathlib

import quiz

GITHUB_GRAPHQL_API = "https://api.github.com/graphql"
GITHUB_API = "https://api.github.com"


log = logging.getLogger(__name__)


def get_schema(*, auth, url):
    schema_path = (
        pathlib.Path(__file__).parent / ".cache/github_schema.json"
    ).resolve()
    schema_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        log.debug("Loading schema from file...")
        schema = quiz.Schema.from_path(schema_path, module=__name__)
        log.debug("Done!")
    except FileNotFoundError:
        log.debug(f"Failed - fallback to load from {url}")
        log.debug("Loading...")
        schema = quiz.Schema.from_url(url, auth=auth, module=__name__)
        schema.to_path(schema_path)
        log.debug("Done!")
    return schema


def load_auth():
    token_path = pathlib.Path("~/.gittoken").expanduser()
    try:
        user, token = token_path.read_text().strip().split()
    except FileNotFoundError:
        sys.exit('No ~/.gittoken file found. Please create one containing "<username> <api token>"')
    except ValueError:
        sys.exit('~/.gittoken file found, but wrong format. Should be "<username> <api token>"')
    return (user, token)
