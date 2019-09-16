import argparse
import asyncio
import csv
import logging
import pathlib


log = logging.getLogger('pr-test-checker')
log.addHandler(logging.FileHandler('/tmp/pr-test-checker.log'))
log.setLevel(logging.DEBUG)

try:
    import aiohttp
except ImportError:
    import sys
    sys.exit('aiohttp failed to import. Try `{sys.executable} -m pip install --user aiohttp` first')

parser = argparse.ArgumentParser()
parser.add_argument('file', type=argparse.FileType('r'))


async def has_test_files_changed(*, pr, session):
    url = f'https://api.github.com/repos/saltstack/salt/pulls/{pr}/files'
    log.debug('Checking %r', url)
    # TODO: change commit token to read from env/file
    headers = {'Authorization': 'token aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'}
    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            data = await response.json()
            files_changed = [change['filename'] for change in data]
            return any(filename.startswith('tests/') for filename in files_changed)
        else:
            log.warning('Unable to find PR %r', pr)
            log.warning('Failure %r', await response.json())
            return None


async def do_it(*, file):
    reader = csv.DictReader(file)
    ordered_prs = [row['pr'] for row in reader]
    has_tests = {}
    async with aiohttp.ClientSession() as session:
        for pr in ordered_prs:
            has_tests[pr] = await has_test_files_changed(pr=pr, session=session)

    for pr in ordered_prs:
        print(f'{"YES" if has_tests[pr] else "NO"}\t=IF(INDIRECT(ADDRESS(ROW(), 2))="{pr}", "OK", "OOPS")')


if __name__ == '__main__':
    args = parser.parse_args()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(do_it(file=args.file))
