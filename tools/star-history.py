import json
import statistics
import pathlib
import sys

import quiz
import git.util

from collections import namedtuple
from datetime import datetime, timedelta

CACHE_FILE = pathlib.Path('.cache/stardown.json')
Star = namedtuple('Star', 'user,starred_at')
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


def get_all_stars_ever(force_reload=False):
    auth = git.util.load_auth()
    schema = git.util.get_schema(auth=auth, url=git.util.GITHUB_GRAPHQL_API)
    owner = "saltstack"
    reponame = "salt"

    _ = quiz.SELECTOR
    end_cursor = ""
    stars = load_from_cache()
    if stars and not force_reload:
        return stars
    while end_cursor is not None:
        star_kwargs = {"first": 100}
        if end_cursor:
            star_kwargs["after"] = end_cursor
        # fmt: off
        query = schema.query[
            _
            .repository(owner=owner, name=reponame)[
                _
                .stargazers(**star_kwargs)[
                    _
                    ('page_info').pageInfo[
                        _
                        ('end_cursor').endCursor
                    ]
                    .edges[
                        _
                        .node[
                            _
                            .login
                            ('created_at').createdAt
                        ]
                    ]
                ]
            ]
        ]
        # fmt: on
        #result = quiz.execute(query, git.util.GITHUB_GRAPHQL_API, auth=auth)
        #end_cursor = result.repository.pull_requests.page_info.end_cursor

        # JSON style for dumping
        print("Requesting", star_kwargs, file=sys.stderr)
        result = quiz.execute(str(query), git.util.GITHUB_GRAPHQL_API, auth=auth)
        end_cursor = result['repository']['stargazers']['page_info'].get('end_cursor')
        stars.extend(result['repository']['stargazers']['edges'])
    dump_to_cache(stars)
    return stars


def simplify(star):
    return Star(
            user=star['node']['login'],
            starred_at=datetime.strptime(star['node']['created_at'], TIMESTAMP_FMT),
    )


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


def stars_open_during_month(*, stars, year, month):
    month_start = datetime(year=year, month=month, day=1)
    # Take the beginning of the month and add 32 days to make sure we're
    # in the next month. Replace the days with 1 to get midnight of the
    # next month.
    next_month = (month_start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)

    # A PR was open during the month if it was created any time before the
    # month was over, and it was closed after the month started.
    starred_this_month = 0
    for star in stars:
        if month_start <= star.starred_at < next_month:
            starred_this_month += 1
    return f'starred this month: {starred_this_month}'


def burndown(*, stars):
    print()
    print('Total stars:', len(stars))
    oldest = min((star.starred_at, star) for star in stars)
    year = oldest[0].year
    month = oldest[0].month
    this_year = datetime.now().year
    this_month = datetime.now().month
    while year < this_year or (year == this_year and month <= this_month):
        print(f'{year}-{month:>02}:', stars_open_during_month(stars=stars, year=year, month=month))
        month += 1
        if month > 12:
            month = 1
            year += 1



def do_it():  # Shia LeBeouf
    stars = get_all_stars_ever(force_reload=False)
    stars = [simplify(star) for star in stars]
    print('*'*50)
    #print('All-time stargazer stats')
    #print('========================')
    #show_stats(stars=stars)
    #return
    #todayte = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    #tomorrow = todayte+timedelta(days=1)
    #last_week = todayte-timedelta(days=7)
    #two_weeks_back = todayte - timedelta(days=14)
    #last_month = last_week - timedelta(days=30)
    #print(f'\nPRs opened & merged between {last_week} and {tomorrow}')
    #show_stats(prs=merged_prs, start_limit=last_week, end_limit=tomorrow)
    #print(f'\nPRs opened & merged between {two_weeks_back} and {tomorrow}')
    #show_stats(prs=merged_prs, start_limit=two_weeks_back, end_limit=tomorrow)
    #print(f'\nPRs opened & merged between {last_month} and {tomorrow}')
    #show_stats(prs=merged_prs, start_limit=last_month, end_limit=tomorrow)


    burndown(stars=stars)


if __name__ == '__main__':
    do_it()
