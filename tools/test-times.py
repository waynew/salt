'''
Test times from Jenkins
'''
import logging
import os

import requests
import requests.auth

from collections import Counter

log = logging.getLogger()

JENKINS_ENV = os.environ.get('JENKINS_ENV', 'jenkinsci-staging')
JENKINS_A_ENV = os.environ.get(
    'JENKINS_A_ENV', os.environ.get('JENKINS_ENV', 'jenkinsci')
)
JENKINS_B_ENV = os.environ.get('JENKINS_B_ENV', JENKINS_ENV)
BRANCH_A_FORMAT = (
    f'https://{JENKINS_A_ENV}.saltstack.com/job/{{branch}}/view/All/api/json'
)
BRANCH_B_FORMAT = (
    f'https://{JENKINS_B_ENV}.saltstack.com/job/{{branch}}/view/All/api/json'
)
TEST_A_BUILD_FORMAT = (
    f'https://{JENKINS_A_ENV}.saltstack.com/job/{{branch}}/job/{{suite}}/api/json'
)
TEST_B_BUILD_FORMAT = (
    f'https://{JENKINS_B_ENV}.saltstack.com/job/{{branch}}/job/{{suite}}/api/json'
)
TEST_A_REPORT_FORMAT = (
    'https://{JENKINS_A_ENV}.saltstack.com/job/{{branch}}/job'
    '/{suite}/{build_number}/testReport/api/json'
)
TEST_A_REPORT_FORMAT = (
    'https://{JENKINS_B_ENV}.saltstack.com/job/{{branch}}/job'
    '/{suite}/{build_number}/testReport/api/json'
)


def all_jobs(branches):
    for branch in branches:
        uri = ('https://jenkinsci.saltstack.com/job/{branch}/view/All/api/json').format(
            branch=branch
        )
        log.debug("Fetching builds for branch:%s url: %s", branch, uri)
        resp = requests.get(
            uri,
            headers={'accept': 'application/json'},
            # auth=requests.auth.HTTPBasicAuth(user, password),
        )
        data = resp.json()
        for job in data['jobs']:
            if job['color'] == 'red':
                yield job['url']


    uri = (
        'https://jenkinsci-staging.saltstack.com/job/{branch}/job' '/{suite}/api/json'
    ).format(branch=branch, suite=suite)
    resp = requests.get(
        uri,
        headers={'accept': 'application/json'},
        # auth=requests.auth.HTTPBasicAuth(user, password),
    )
    log.debug('Fetching builds for branch: %s suite: %s uri: %s', branch, suite, uri)
    if resp.status_code != 200:
        log.error(
            'Unable to fetch builds: %s %s %s %s', branch, suite, uri, resp.status_code
        )
        return
    for build in sorted(resp.json()['builds'], key=lambda x: x['number'], reverse=True):
        yield build['url']


def test_results(env, branch, suite, number=None):
    uri = f'https://{env}.saltstack.com/job/{branch}/job/{suite}/api/json'
    r = requests.get(uri)
    if r.status_code != 200:
        raise Exception(
            'Unable to fetch builds: %s %s %s %s %s', env, branch, suite, uri, r.status_code
        )
    for build in sorted(r.json()['builds'], key=lambda x: x['number'], reverse=True):
        build_number = build['number']
        if number and number != build_number:
            continue
        uri = (
            f'https://{env}.saltstack.com/job/{branch}/job/{suite}/{build_number}'
             '/testReport/api/json'
        )
        r = requests.get(uri)
        if r.status_code != 200:
            log.warning('No test results found at %r', uri)
        else:
            for suite in r.json()['suites']:
                for case in suite['cases']:
                    yield case


def do_it():
    count = 0
    a = {'env': 'jenkinsci-staging', 'branch': 'neon', 'suite': 'salt-debian-8-py3'}
    b = {'env': 'jenkinsci', 'branch': '2019.2.1', 'suite': 'salt-debian-8-py3'}
    a_results = Counter()
    b_results = Counter()
    for result in test_results(**a):
        a_results[result['className']] += result['duration'] / 60  # duration is in seconds

    for result in test_results(**b):
        b_results[result['className']] += result['duration'] / 60  # duration is in seconds

    print(len(b_results))


    comparisons = {}
    for name in a_results:
        comparisons[name] = {'a': a_results[name], 'b': b_results[name]}

#  A env              A branch  A duration  B duration   B env               B branch
#  jenkinsci-staging  neon      0.000       41.658       jenkinsci-staging   neon
#  jenkinsci-staging  neon      0.000       27.883       jenkinsci           neon

    print(f'{"Test Name":<85} {"A env":<18} {"A branch":<10} {"A duration":<10} {"B duration":<10} {"B env":<18} {"B branch":<10}')
    a_total = b_total = 0
    for name, duration in a_results.most_common(100):
        a_duration = a_results[name]
        if name.startswith('tests.') and not b_results[name]:
            name = name.partition('.')[-1]
        b_duration = b_results[name]
        a_total += a_duration
        b_total += b_duration
        print(f"{name:<85} {a['env']:<18} {a['branch']:<10} {a_duration:>10,.3f} {b_duration:>10,.3f} {b['env']:<18} {b['branch']:<10}")

    print(f'A total: {a_total:4.3f} / B total: {b_total:4.3f}')
    print('*'*50)
    print()
    print(f'{"Test Name":<85} {"A env":<18} {"A branch":<10} {"A duration":<10} {"B duration":<10} {"B env":<18} {"B branch":<10}')
    a_total = b_total = 0
    for name, duration in b_results.most_common(100):
        b_duration = b_results[name]
        if not name.startswith('tests.') and not a_results[name]:
            name = 'tests.'+name
        a_duration = a_results[name]
        a_total += a_duration
        b_total += b_duration
        print(f"{name:<85} {a['env']:<18} {a['branch']:<10} {a_duration:>10,.3f} {b_duration:>10,.3f} {b['env']:<18} {b['branch']:<10}")
    print(f'A total: {a_total:4.3f} / B total: {b_total:4.3f}')

    diffs = Counter()
    for name in a_results:
        a_duration = a_results[name]
        if name.startswith('tests.') and not b_results[name]:
            name = name.partition('.')[-1]
        b_duration = b_results[name]
        diff = a_duration - b_duration
        diffs[name] = diff

    for name, duration in diffs.most_common(10):
        print(f'{duration:>7,.3f} {name}')

    print('*'*50, end='\n'*2)
    for name, duration in list(reversed(diffs.most_common()))[:10]:
        print(f'{duration:>7,.3f} {name}')


def builds(branch, suite, number_of_builds=1):
    uri = (
        'https://jenkinsci-staging.saltstack.com/job/{branch}/job' '/{suite}/api/json'
    ).format(branch=branch, suite=suite)
    resp = requests.get(
        uri,
        headers={'accept': 'application/json'},
    )
    log.debug('Fetching builds for branch: %s suite: %s uri: %s', branch, suite, uri)
    if resp.status_code != 200:
        log.error(
            'Unable to fetch builds: %s %s %s %s', branch, suite, uri, resp.status_code
        )
        return
    for build in sorted(resp.json()['builds'], key=lambda x: x['number'], reverse=True):
        yield build['url']


if __name__ == '__main__':
    logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(message)s')
    do_it()
