#!/usr/bin/env python3.7
"""Test Failure Report

Usage:
    test-failure-report.py [-h --url=JENKINS_URL --format=FORMAT] JOB PROJECT [START] [END]

Produce a report of test failures for the provided range, defaults to the
last day, i.e. 00:00:00 of the previous day, until now.

Report will be printed to STDOUT. The default report format is a tsv, for
easy copy/pasting into a spreadsheet application.

Arguments:
    JOB         The job/branch, e.g. neon, or 2019.2.1
    PROJECT     The project/arch, e.g. salt-arch-py2, or salt-centos7-py2
    START       The start time (inclusive, in UTC) to filter by. Defaults
                to yesterday at midnight, UTC.
    END         The end time (inclusive, in UTC) to filter by. Defaults to
                tonight ad midnight, UTC.

Options:
    -h                      Print this message and quit
    --url=JENKINS_URL       The Jenkins root URL [default: https://jenkinsci.saltstack.com]
    --format=FORMAT         Output format, csv or tsv. [default: tsv]
"""

import asyncio
import csv
import io
import sys


from datetime import datetime, timedelta, timezone

try:
    from docopt import docopt
except ImportError:
    sys.exit(
        f"docopt required. Try `{sys.executable} -m pip install --user docopt` to install"
    )

try:
    import aiohttp
except ImportError:
    sys.exit(
        f"aiohttp required. Try `{sys.executable} -m pip install --user aiohttp` to install"
    )


async def fetch_project(*, session, jenkins_url, job, project):
    url = f'{jenkins_url.rstrip("/")}/job/{job}/job/{project}/api/json'
    async with session.get(url) as response:
        result = await response.json()
        return result


async def fetch_build(*, session, build_url):
    async with session.get(f'{build_url}/api/json') as response:
        return await response.json()


async def fetch_builds(*, session, builds):
    for build in builds:
        yield await fetch_build(session=session, build_url=build['url'])


async def fetch_test_report(*, session, build_url):
    url = f'{build_url.rstrip("/")}/testReport/api/json'
    async with session.get(url) as response:
        if response.status == 200:
            return await response.json()
        else:
            return None


async def fetch_test_failures(*, jenkins_url, job, project, start, end):
    failures = []
    async with aiohttp.ClientSession() as session:
        data = await fetch_project(
            session=session, jenkins_url=jenkins_url, job=job, project=project
        )
        async for build in fetch_builds(session=session, builds=data['builds']):
            if build['result'].lower() == 'failure':
                build_ts = datetime.fromtimestamp(
                    build['timestamp'] / 1000, timezone.utc
                )
                if start <= build_ts <= end:
                    test_report = await fetch_test_report(
                        session=session, build_url=build['url']
                    )
                    if test_report is None:
                        failures.append({
                            'job': job,
                            'project': project,
                            'test_case': 'Failed with no test results',
                        })
                    else:
                        for suite in test_report['suites']:
                            for case in suite['cases']:
                                if case['status'].lower() == 'failed':
                                    failures.append({
                                        'job': job,
                                        'project': project,
                                        'test_case': case['className'],
                                        'duration': case['duration'],
                                    })
    return failures


def produce_report(*, jenkins_url, job, project, start, end, report_format):
    loop = asyncio.get_event_loop()
    result, = loop.run_until_complete(
        asyncio.gather(
            fetch_test_failures(
                jenkins_url=jenkins_url, job=job, project=project, start=start, end=end
            )
        )
    )
    delimiter = '\t' if report_format == 'tsv' else ','
    report = io.StringIO()
    writer = csv.DictWriter(report, delimiter=delimiter, fieldnames=('job', 'project', 'test_case', 'duration'))
    writer.writeheader()
    for row in result:
        writer.writerow(row)
    report.seek(0)
    return report


def parse_start_and_end(*, start, end):
    now = datetime.now()
    utcnow = datetime.now(timezone.utc).replace(microsecond=now.microsecond)
    since_midnight = now - now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday = utcnow - since_midnight - timedelta(days=1)
    tomorrow = yesterday + timedelta(days=2) - timedelta(microseconds=1)
    fmt = '%Y-%m-%d %H:%M %z'
    if start:
        try:
            start = datetime.strptime(start+' +0000', fmt)
        except ValueError:
            sys.exit(f'{start!r} not in format "%Y-%m-%d %H:%M"')
    else:
        start = yesterday

    if end:
        try:
            end = datetime.strptime(end+' +0000', fmt)
        except ValueError:
            sys.exit(f'{end!r} not in format "%Y-%m-%d %H:%M"')
    else:
        end = tomorrow
    result = {'start': start, 'end': end}
    return result


if __name__ == "__main__":
    args = docopt(__doc__)
    report = produce_report(
        jenkins_url=args["--url"],
        job=args["JOB"],
        project=args["PROJECT"],
        report_format=args['--format'],
        **parse_start_and_end(start=args['START'], end=args['END']),
    )
    print(report.read())
