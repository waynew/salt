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
JENKINS_BRANCH = os.environ.get('JENKINS_BRANCH', 'neon')
JENKINS_URL = f'{JENKINS_ENV}/job/{JENKINS_BRANCH}/view/All/api/json'
# Jenkins uses an integer timestamp, instead of floating point for microsecs
JENKINS_TIMESTAMP_OFFSET = 1000


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


async def get_build_status(*, job, session):
    async with session.get(job['url']+'api/json') as r:
        data = await r.json()
    branch_name = data['name']
    last_completed_build_url = data['lastCompletedBuild']['url']+'api/json'
    async with session.get(last_completed_build_url) as r:
        data = await r.json()
    #import pprint; pprint.pprint(data)
    #import os; os.abort()
    #return data
    start = datetime.datetime.fromtimestamp(
        data['timestamp']/JENKINS_TIMESTAMP_OFFSET
    )
    start_reason = get_start_reason(data)
    duration = datetime.timedelta(seconds=data['duration']/1000)
    end = start+duration
    build_info = {
        'branch': branch_name,
        'number': data['number'],
        'start': start,
        'end': end,
        'result': data['result'],
        'duration': duration,
        'start_reason': get_start_reason(data),
        'executor': await find_executor(job_url=data['url'], session=session),
        'url': data['url'],
    }
    return build_info


async def collect_failures():
    async with aiohttp.ClientSession() as session:
        async with session.get(JENKINS_URL) as resp:
            body = await resp.json()
            jobs = body['jobs']
            recent_builds = [
                asyncio.create_task(get_build_status(
                    job=job,
                    session=session,
                ))
                for job in jobs
            ]
        done, pending = await asyncio.wait(recent_builds)
        return list(t.result() for t in done)


def dump_failures(failures):
    writer = csv.DictWriter(sys.stdout, fieldnames=failures[0].keys(), delimiter='\t')
    writer.writeheader()
    for result in failures:
        writer.writerow(result)


def do_it():
    loop = asyncio.get_event_loop()
    failures = loop.create_task(collect_failures())
    loop.run_until_complete(failures)
    dump_failures(failures.result())


if __name__ == '__main__':
    do_it()
