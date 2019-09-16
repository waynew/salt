import asyncio
import csv
import datetime
import itertools
import os
import re
import sys

from collections import defaultdict

try:
    import aiohttp
except ImportError:
    sys.exit(f'Missing aiohttp - try `{sys.executable} -m pip install --user aiohttp`')


JENKINS_ENV = os.environ.get('JENKINS_ENV', 'https://jenkinsci.saltstack.com')
JENKINS_BRANCH = os.environ.get('JENKINS_BRANCH', '2019.2.1')
JENKINS_URL = f'{JENKINS_ENV}/job/{JENKINS_BRANCH}/view/All/api/json'
# Jenkins uses an integer timestamp, instead of floating point for microsecs
JENKINS_TIMESTAMP_OFFSET = 1000
# Check all builds starting from 4AM UTC 08/13-> 11AM UTC
YESTERDAY = datetime.datetime.now() - datetime.timedelta(hours=24)
START_LIMIT = datetime.datetime(2019, 8, 14, 4, 0)
END_LIMIT = datetime.datetime(2019, 8, 14, 15, 59)


async def get_job(session, job_url):
    async with session.get(job_url+'api/json') as r:
        return await r.json()


def get_start_reason(data):
    for action in data.get('actions', []):
        if action.get('_class', '').endswith('CauseAction'):
            for c in action.get('causes'):
                if 'shortDescription' in c:
                    return c['shortDescription']
    return None


async def find_executor(*, job_url, session, bytes_to_read=4000):
    async with session.get(job_url+'consoleText') as r:
        console_data = (await r.content.read(bytes_to_read)).decode()
        data = re.search(r'Running on (.*) in ', console_data)
        if data:
            return data.groups()[0]


async def get_recent_build_times(*, job, session, start_limit_inclusive=None):
    start_limit = start_limit_inclusive or YESTERDAY
    async with session.get(job['url']+'api/json') as r:
        data = await r.json()
    previous_build = data['lastBuild']
    branch_name = data['name']
    build_is_after_limit = True
    build_info = []
    while build_is_after_limit:
        async with session.get(previous_build['url']+'api/json') as r:
            data = await r.json()
            start = datetime.datetime.fromtimestamp(
                data['timestamp']/JENKINS_TIMESTAMP_OFFSET
            )
            previous_build = data['previousBuild']
            if start < START_LIMIT:
                build_is_after_limit = False
            elif START_LIMIT <= start <= END_LIMIT:
                start_reason = get_start_reason(data)
                duration = datetime.timedelta(seconds=data['duration']/1000)
                end = start+duration
                build_info.append({
                    'branch': branch_name,
                    'number': data['number'],
                    'start': start,
                    'end': end,
                    'result': data['result'],
                    'duration': duration,
                    'start_reason': get_start_reason(data),
                    'executor': await find_executor(job_url=data['url'], session=session),
                })
    return build_info


async def collect_timeline():
    async with aiohttp.ClientSession() as session:
        async with session.get(JENKINS_URL) as resp:
            body = await resp.json()
            jobs = body['jobs']
            recent_builds = [
                asyncio.create_task(get_recent_build_times(
                    job=job,
                    session=session,
                ))
                for job in jobs
            ]
        done, pending = await asyncio.wait(recent_builds)
        return list(itertools.chain.from_iterable(t.result() for t in done))


def dump_timeline(tl):
    by_build = defaultdict(list)
    earliest = tl[0]['start']
    latest = tl[0]['end']
    with open('/tmp/report.tsv', 'w') as f:
        writer = csv.DictWriter(f, fieldnames=tl[0].keys(), delimiter='\t')
        writer.writeheader()
        for result in tl:
            writer.writerow(result)
            earliest = min(result['start'], earliest)
            latest = max(result['end'], latest)
            by_build[result['branch']].append(result)
    length = 80


def do_it():
    loop = asyncio.get_event_loop()
    timeline = loop.create_task(collect_timeline())
    loop.run_until_complete(timeline)
    dump_timeline(timeline.result())


if __name__ == '__main__':
    do_it()
