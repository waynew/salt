import json
import statistics
import pathlib
import sys

import quiz
import git.util

from collections import namedtuple, defaultdict
from datetime import datetime, timedelta

CACHE_FILE = pathlib.Path('.cache/pr-burndown.json')
Pr = namedtuple('Pr', 'author,number,state,created_at,closed_at,reviews')
TIMESTAMP_FMT = '%Y-%m-%dT%H:%M:%SZ'


def load_from_cache():
    if CACHE_FILE.exists():
        try:
            with CACHE_FILE.open('r') as f:
                return json.load(f)
        except ValueError:
            print('Unable to load json from cache', file=sys.stderr)
    else:
        print('No cache file exists', file=sys.stderr)
    return []


def dump_to_cache(data):
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with CACHE_FILE.open('w') as f:
        json.dump(data, f)


def get_all_pull_requests_ever(force_reload=False):
    auth = git.util.load_auth()
    schema = git.util.get_schema(auth=auth, url=git.util.GITHUB_GRAPHQL_API)
    owner = "saltstack"
    reponame = "salt"

    _ = quiz.SELECTOR
    end_cursor = ""
    pull_requests = load_from_cache()
    if pull_requests and not force_reload:
        return pull_requests
    while end_cursor is not None:
        pr_kwargs = {"first": 100}
        if end_cursor:
            pr_kwargs["after"] = end_cursor
        # fmt: off
        query = schema.query[
            _
            .repository(owner=owner, name=reponame)[
                _
                ('pull_requests').pullRequests(**pr_kwargs)[
                    _
                    ('page_info').pageInfo[
                        _
                        ('end_cursor').endCursor
                    ]
                    .edges[
                        _
                        .node[
                            _
                            .state
                            .number
                            .author[
                                _
                                .login
                            ]
                            ('created_at').createdAt
                            ('closed_at').closedAt
                            .reviews(first=100)[
                                _
                                .nodes[
                                    _
                                    .state
                                    ('created_at').createdAt
                                    ('submitted_at').submittedAt
                                    ('updated_at').updatedAt
                                    .author[
                                        _
                                        .login
                                    ]
                                ]
                            ]
                        ]
                    ]
                ]
            ]
        ]
        # fmt: on
        #result = quiz.execute(query, git.util.GITHUB_GRAPHQL_API, auth=auth)
        #end_cursor = result.repository.pull_requests.page_info.end_cursor

        # JSON style for dumping
        print("Requesting", pr_kwargs, file=sys.stderr)
        result = quiz.execute(str(query), git.util.GITHUB_GRAPHQL_API, auth=auth)
        end_cursor = result['repository']['pull_requests']['page_info'].get('end_cursor')
        pull_requests.extend(result['repository']['pull_requests']['edges'])
    dump_to_cache(pull_requests)
    return pull_requests


def simplify(pr):
    PR = Pr(
        author=(pr['node'].get('author') or {}).get('login'),
        number=pr['node']['number'],
        state=pr['node']['state'],
        created_at=datetime.strptime(pr['node']['created_at'], TIMESTAMP_FMT),
        closed_at=datetime.strptime(pr['node']['closed_at'], TIMESTAMP_FMT) if pr['node']['closed_at'] else None,
        reviews=pr['node']['reviews']['nodes'],
    )
    if PR.author is None:
        pass # author is "ghost" - GH account was deleted breakpoint()
    return PR


def get_max_merge_time(prs):
    max_time = prs[0].closed_at-prs[0].created_at
    max_pr = prs[0]
    for pr in prs:
        merge_time = pr.closed_at - pr.created_at
        if merge_time > max_time:
            max_pr = pr
            max_time = merge_time
    return str(max_time), max_pr


def get_min_merge_time(prs):
    min_time = prs[0].closed_at-prs[0].created_at
    min_pr = prs[0]
    for pr in prs:
        merge_time = pr.closed_at - pr.created_at
        if merge_time < min_time:
            min_pr = pr
            min_time = merge_time
    return str(min_time), min_pr


def get_ave_merge_time(prs):
    ave_merge_time = sum((pr.closed_at - pr.created_at for pr in prs), timedelta(0)) / len(prs)
    return ave_merge_time


def get_median_merge_time(prs):
    return statistics.median(pr.closed_at - pr.created_at for pr in prs)


def compute_stats(*, start_limit, end_limit):
    ...


def show_stats(*, prs, start_limit, end_limit):
    prs = [pr for pr in prs if start_limit <= pr.created_at and pr.closed_at <= end_limit]
    print('Max merge time:', get_max_merge_time(prs)[0])
    print('Min merge time:', get_min_merge_time(prs)[0])
    print('Average merge time:', get_ave_merge_time(prs))
    print('Median merge time:', get_median_merge_time(prs))


def prs_open_during_month(*, prs, year, month):
    month_start = datetime(year=year, month=month, day=1)
    # Take the beginning of the month and add 32 days to make sure we're
    # in the next month. Replace the days with 1 to get midnight of the
    # next month.
    next_month = (month_start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)

    # A PR was open during the month if it was created any time before the
    # month was over, and it was closed after the month started.
    closed_this_month = 0
    merged_this_month = 0
    open_during_the_month = 0
    created_this_month = 0
    for pr in prs:
        if pr.state != 'OPEN' and month_start <= pr.closed_at < next_month:
            if pr.state == 'MERGED':
                merged_this_month += 1
            elif pr.state == 'CLOSED':
                closed_this_month += 1
        if pr.created_at < next_month and (pr.state == 'OPEN' or month_start < pr.closed_at):
            open_during_the_month += 1
        if month_start <= pr.created_at < next_month:
            created_this_month += 1
    delta_this_month = created_this_month - merged_this_month - closed_this_month
    green = '[32m'
    red = '[31m'
    return f'open: {open_during_the_month:>4}, created: {created_this_month:>4}, merged: {merged_this_month:>4}, closed: {closed_this_month:>4}, change: {green if delta_this_month < 1 else red}{delta_this_month:>+4}[0m'


def burndown(*, open_prs, merged_prs, closed_prs):
    print()
    print('Current open PRs:', len(open_prs))
    oldest = min((pr.created_at, pr) for pr in open_prs + merged_prs)
    year = oldest[0].year
    month = oldest[0].month
    this_year = datetime.now().year
    this_month = datetime.now().month
    while year < this_year or (year == this_year and month <= this_month):
        print(f'{year}-{month:>02}:', prs_open_during_month(prs=open_prs+merged_prs+closed_prs, year=year, month=month))
        month += 1
        if month > 12:
            month = 1
            year += 1
    print(oldest)


def do_it():  # Shia LeBeouf
    prs = get_all_pull_requests_ever(force_reload=False)
    prs = [simplify(pr) for pr in prs]
    merged_prs = [pr for pr in prs if pr.state == 'MERGED']
    closed_prs = [pr for pr in prs if pr.state == 'CLOSED']
    open_prs = [pr for pr in prs if pr.state == 'OPEN']
    print(f'Checksum: merged({len(merged_prs)})+closed({len(closed_prs)})+open({len(open_prs)}) =', len(merged_prs) + len(closed_prs) + len(open_prs), 'total =', len(prs))
    print('*'*50)
    print('All-time PR stats')
    print('=================')
    show_stats(prs=merged_prs, start_limit=min(pr.created_at for pr in merged_prs), end_limit=max(pr.closed_at for pr in merged_prs))
    todayte = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = todayte+timedelta(days=1)
    last_week = todayte-timedelta(days=7)
    two_weeks_back = todayte - timedelta(days=14)
    last_month = last_week - timedelta(days=30)
    print(f'\nPRs opened & merged between {last_week} and {tomorrow}')
    show_stats(prs=merged_prs, start_limit=last_week, end_limit=tomorrow)
    print(f'\nPRs opened & merged between {two_weeks_back} and {tomorrow}')
    show_stats(prs=merged_prs, start_limit=two_weeks_back, end_limit=tomorrow)
    print(f'\nPRs opened & merged between {last_month} and {tomorrow}')
    show_stats(prs=merged_prs, start_limit=last_month, end_limit=tomorrow)


    burndown(open_prs=open_prs, merged_prs=merged_prs, closed_prs=closed_prs)


def break_prs_by_core_or_community(*, employees, prs, year, month):
    month_start = datetime(year=year, month=month, day=1)
    # Take the beginning of the month and add 32 days to make sure we're
    # in the next month. Replace the days with 1 to get midnight of the
    # next month.
    next_month = (month_start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
    by_employee = []
    by_community = []
    for pr in prs:
        if month_start <= pr.created_at < next_month:
            if pr.author in employees:
                by_employee.append(pr)
            else:
                by_community.append(pr)
    return by_employee, by_community


def do_it_two():
    with open('employees.txt') as f:
        employees = set(e.strip() for e in f)
    prs = get_all_pull_requests_ever(force_reload=False)
    prs = [simplify(pr) for pr in prs]
    merged_prs = [pr for pr in prs if pr.state == 'MERGED']
    closed_prs = [pr for pr in prs if pr.state == 'CLOSED']
    open_prs = [pr for pr in prs if pr.state == 'OPEN']

    oldest = min((pr.created_at, pr) for pr in prs)

    year = oldest[0].year
    month = oldest[0].month
    this_year = datetime.now().year
    this_month = datetime.now().month
    checksum = 0
    print(f"Month\t# of PRs opened by community members\t# of unique contributors\t# of PRs opened by current employees\t# of unique employee contributors")
    while year < this_year or (year == this_year and month <= this_month):
        opened_by_current_employees, opened_by_community = break_prs_by_core_or_community(employees=employees, prs=prs, year=year, month=month)
        checksum += len(opened_by_current_employees) + len(opened_by_community)
        unique_employees = len(set(e.author for e in opened_by_current_employees))
        unique_community = len(set(e.author for e in opened_by_community))
        print(f"{year}-{month}\t{len(opened_by_community)}\t{unique_community}\t{len(opened_by_current_employees)}\t{unique_employees}")
        month += 1
        if month > 12:
            month = 1
            year += 1
    print('Total:', checksum)

    print(f'Checksum: merged({len(merged_prs)})+closed({len(closed_prs)})+open({len(open_prs)}) =', len(merged_prs) + len(closed_prs) + len(open_prs), 'total =', len(prs))

    by_author = defaultdict(dict)
    for pr in prs:
        by_author[pr.author][pr.number] = pr

    #for author in reversed(sorted(by_author, key=lambda x: len(by_author[x]))):
    #    print(author, len(by_author[author]))
    todayte = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    first_of_month = todayte.replace(day=1)


if __name__ == '__main__':
    do_it_two()
