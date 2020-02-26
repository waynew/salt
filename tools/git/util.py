import argparse
import logging
import pathlib

import quiz

GITHUB_GRAPHQL_API = "https://api.github.com/graphql"


log = logging.getLogger(__name__)


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
        log.debug("Loading...")
        schema = quiz.Schema.from_url(url, auth=auth)
        schema.to_path(schema_path)
        log.debug("Done!")
    return schema


def load_auth():
    token_path = pathlib.Path("~/.gittoken").expanduser()
    user, token = token_path.read_text().strip().split()
    return (user, token)
