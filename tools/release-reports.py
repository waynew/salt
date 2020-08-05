import subprocess
import datetime
import quiz
import git.util

from pathlib import Path

REPO_DIR = Path('~/programming/salt').expanduser()


def get_last_tags(*, num_of_tags=5):
    cmd = ['git', 'tag', '-l', '--sort=-creatordate', "--format=%(creatordate:short):%(refname:short)"]
    ret = subprocess.run(cmd, cwd=REPO_DIR, capture_output=True)
    tags = [line.split(':', maxsplit=1) for line in ret.stdout.decode().splitlines() if 'rc' not in line and 'docs' not in line][:num_of_tags]
    return tags


def issues_created_around(*, start_date, end_date):
    '''
    Get issues that were created between start date and end date inclusive.
    '''

    auth = git.util.load_auth()
    schema = git.util.get_schema(auth=auth, url=git.util.GITHUB_GRAPHQL_API)
    schema.populate_module()
    class FilterBy(git.util.IssueFilters):
        def __init__(self, since):
            super().__init__()
            self.since = since
        def __gql_dump__(self):
            return f'{{since: "{self.since:%Y-%m-%dT00:00:00}"}}'

    owner = "saltstack"
    reponame = "salt"
    _ = quiz.SELECTOR
    end_cursor = ""
    pr_numbers = []
    count = 0
    while end_cursor is not None:
        count += 1
        card_kwargs = {"first": 100}
        if end_cursor:
            card_kwargs["after"] = end_cursor
        # fmt: off
        query = schema.query[
            _
            .repository(owner=owner, name=reponame)[
                _
                .issues(first=100, filterBy=FilterBy(since=start_date))[
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
        result = quiz.execute(query, git.util.GITHUB_GRAPHQL_API, auth=auth)
        end_cursor = result.repository.issues.page_info.end_cursor
        print(f'Looked through {100*count} issues')
        for edge in result.repository.issues.edges:
            issue = edge.node
            issue.created_at = datetime.datetime.strptime(issue.created_at, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=datetime.timezone.utc)
            if start_date <= issue.created_at.date() <= end_date:
                yield issue

def do_it():
    for date, tag in get_last_tags(num_of_tags=2):
        date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
        print(date, tag)
        print('\t', len(list(issues_created_around(start_date=date, end_date=date))))

if __name__  == '__main__':
    do_it()
