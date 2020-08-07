import csv
import datetime
import io
import pickle
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import quiz

import git.util

REPO_DIR = Path("~/programming/salt").expanduser()


class Tag:
    def __init__(self, number, creation_date):
        self.number = number
        self.creation_date = creation_date
        self._issues = []

    def __repr__(self):
        return f"Tag(number={self.number!r}, creation_date={self.creation_date!r}"

    @property
    def minus_two_weeks(self):
        return self.creation_date - datetime.timedelta(days=14)

    @property
    def minus_one_week(self):
        return self.creation_date - datetime.timedelta(days=7)

    @property
    def plus_one_week(self):
        return self.creation_date + datetime.timedelta(days=7)

    @property
    def plus_two_weeks(self):
        return self.creation_date + datetime.timedelta(days=14)

    def add(self, issue):
        if self.minus_two_weeks <= issue.created_at.date() <= self.plus_two_weeks:
            self._issues.append(issue)

    @property
    def created_two_weeks_prior(self):
        return [
            issue
            for issue in self._issues
            if self.minus_two_weeks <= issue.created_at.date() < self.minus_one_week
        ]

    @property
    def created_prior_week(self):
        return [
            issue
            for issue in self._issues
            if self.minus_one_week <= issue.created_at.date() < self.creation_date
        ]

    @property
    def created_release_week(self):
        return [
            issue
            for issue in self._issues
            if self.creation_date <= issue.created_at.date() < self.plus_one_week
        ]

    @property
    def created_week_after_release(self):
        return [
            issue
            for issue in self._issues
            if self.plus_one_week <= issue.created_at.date() < self.plus_two_weeks
        ]

    @property
    def close_times(self):
        return {
            "two weeks before": sum(
                (
                    issue.closed_at - issue.created_at
                    for issue in self.created_two_weeks_prior
                    if issue.closed
                ),
                datetime.timedelta(hours=0),
            )
            / len(self.created_two_weeks_prior),
            "week before release": sum(
                (
                    issue.closed_at - issue.created_at
                    for issue in self.created_prior_week
                    if issue.closed
                ),
                datetime.timedelta(hours=0),
            )
            / len(self.created_prior_week),
            "week of release": sum(
                (
                    issue.closed_at - issue.created_at
                    for issue in self.created_release_week
                    if issue.closed
                ),
                datetime.timedelta(hours=0),
            )
            / len(self.created_release_week),
            "week after release": sum(
                (
                    issue.closed_at - issue.created_at
                    for issue in self.created_week_after_release
                    if issue.closed
                ),
                datetime.timedelta(hours=0),
            )
            / len(self.created_week_after_release),
        }


def get_last_tags(*, num_of_tags=5):
    cmd = [
        "git",
        "tag",
        "-l",
        "--sort=-creatordate",
        "--format=%(creatordate:short):%(refname:short)",
    ]
    ret = subprocess.run(cmd, cwd=REPO_DIR, capture_output=True)
    tags = (
        line.split(":", maxsplit=1)
        for line in ret.stdout.decode().splitlines()
        if "rc" not in line and "docs" not in line
    )
    return [
        Tag(
            creation_date=datetime.datetime.strptime(tag[0], "%Y-%m-%d").date(),
            number=tag[1],
        )
        for i, tag in zip(range(num_of_tags), tags)
    ]


def issues_created_around(*, start_date, end_date, force_reload=False):
    """
    Get issues that were created between start date and end date inclusive.
    """

    auth = git.util.load_auth()
    schema = git.util.get_schema(auth=auth, url=git.util.GITHUB_GRAPHQL_API)
    schema.populate_module()
    fname = ".cache/release-report-issues.pkl"
    data = []
    if not force_reload:
        with open(fname, "rb") as f:
            data = pickle.load(f)
            for d in data:
                yield d
    else:

        class FilterBy(git.util.IssueFilters):
            def __init__(self, *, since):
                super().__init__()
                self.since = since

            def __gql_dump__(self):
                return f'{{since: "{self.since:%Y-%m-%dT00:00:00}"}}'

        class OrderBy(git.util.IssueOrder):
            def __init__(self, *, field, direction):
                super().__init__()
                self.field = field
                self.order = direction

            def __gql_dump__(self):
                return f"{{field: {self.field.value}, direction: {self.order.value}}}"

        owner = "saltstack"
        reponame = "salt"
        _ = quiz.SELECTOR
        end_cursor = ""
        pr_numbers = []
        count = 0
        while end_cursor is not None:
            count += 1
            issue_kwargs = {
                "first": 100,
                "filterBy": FilterBy(since=start_date),
                "orderBy": OrderBy(
                    direction=schema.OrderDirection.ASC,
                    field=schema.IssueOrderField.CREATED_AT,
                ),
            }
            if end_cursor:
                issue_kwargs["after"] = end_cursor
            # fmt: off
            query = schema.query[
                _
                .repository(owner=owner, name=reponame)[
                    _
                    .issues(**issue_kwargs)[
                        _
                        .edges[
                            _
                            .node[
                                _
                                .id
                                .author[
                                    _
                                    .login
                                ]
                                .number
                                .title
                                .closed
                                ('closed_at').closedAt
                                ('created_at').createdAt
                            ]
                        ]
                        ('page_info').pageInfo[
                            _
                            ('end_cursor').endCursor
                        ]
                    ]
                ]
            ]
            # fmt: on
            try:
                result = quiz.execute(query, git.util.GITHUB_GRAPHQL_API, auth=auth)
            except quiz.execution.ErrorResponse as e:
                print(e.data, e.errors)
                return
            end_cursor = result.repository.issues.page_info.end_cursor
            print(f"Looked through {100*count} issues, ending at {end_cursor}")
            for edge in result.repository.issues.edges:
                issue = edge.node
                issue.created_at = datetime.datetime.strptime(
                    issue.created_at, "%Y-%m-%dT%H:%M:%SZ"
                ).replace(tzinfo=datetime.timezone.utc)
                if issue.closed:
                    issue.closed_at = datetime.datetime.strptime(
                        issue.closed_at, "%Y-%m-%dT%H:%M:%SZ"
                    ).replace(tzinfo=datetime.timezone.utc)
                if start_date <= issue.created_at.date() <= end_date:
                    data.append(issue)
                    yield issue
    with open(fname, "wb") as f:
        pickle.dump(data, f)


def do_it():
    tags = get_last_tags(num_of_tags=20)
    earliest_date = min(tag.creation_date for tag in tags) - datetime.timedelta(days=14)
    latest_date = max(tag.creation_date for tag in tags) + datetime.timedelta(days=14)
    for issue in issues_created_around(
        start_date=earliest_date,
        end_date=latest_date,
        force_reload="--force-reload" in sys.argv,
    ):
        for tag in tags:
            tag.add(issue)

    if "--csv" not in sys.argv:
        for tag in tags:
            print(f"{tag.number} - {tag.creation_date}")
            print(
                f"\tCreated 2 weeks before: {len(tag.created_two_weeks_prior)} - {sum(1 for i in tag.created_two_weeks_prior if not i.closed)} still open - {tag.close_times['two weeks before']}"
            )
            print(
                f"\tCreated 1 week before: {len(tag.created_prior_week)} - {sum(1 for i in tag.created_prior_week if not i.closed)} still open - {tag.close_times['week before release']}"
            )
            print(
                f"\tCreated week of release: {len(tag.created_release_week)} - {sum(1 for i in tag.created_release_week if not i.closed)} still open - {tag.close_times['week of release']}"
            )
            print(
                f"\tCreated week after release: {len(tag.created_week_after_release)} - {sum(1 for i in tag.created_week_after_release if not i.closed)} still open - {tag.close_times['week after release']}"
            )
    else:
        writer = csv.writer(sys.stdout)
        for tag in tags:
            writer.writerow(
                [
                    tag.number,
                    tag.creation_date,
                    len(tag.created_two_weeks_prior),
                    sum(1 for i in tag.created_two_weeks_prior if not i.closed),
                    len(tag.created_prior_week),
                    sum(1 for i in tag.created_prior_week if not i.closed),
                    len(tag.created_release_week),
                    sum(1 for i in tag.created_release_week if not i.closed),
                    len(tag.created_week_after_release),
                    sum(1 for i in tag.created_week_after_release if not i.closed),
                ]
            )


if __name__ == "__main__":
    do_it()
