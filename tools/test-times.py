'''
Test times from Jenkins
'''
import logging
import os

import requests
import requests.auth

from collections import Counter

log = logging.getLogger()

uri = os.environ.get('JENKINS_URI', 'https://jenkinsci.saltstack.com/api/json')


def all_jobs(branches):
    for branch in branches:
        uri = (
            'https://jenkinsci.saltstack.com/job/{branch}/view/All/api/json'
        ).format(branch=branch)
        log.debug("Fetching builds for branch:%s url: %s", branch, uri)
        resp = requests.get(
            uri,
            headers={'accept': 'application/json'},
            #auth=requests.auth.HTTPBasicAuth(user, password),
        )
        data = resp.json()
        for job in data['jobs']:
            if job['color'] == 'red':
                yield job['url']


def do_it():
    branch = '2019.2.1'
    branch = 'neon'
    times = Counter()
    for job_url in all_jobs([branch]):
        parts = job_url.split('/')
        branch = parts[4]
        suite = parts[6]
        suite = 'salt-centos-7-py2'
        suite = 'salt-centos-6-py2'
        suite = 'salt-centos-6-py2'
        suite = 'salt-debian-8-py3'
        for url in builds(branch, suite, 1):
            parts = url.split('/')
            branch = parts[4]
            suite = parts[6]
            build_number = parts[7]
            has_failures = False
            uri = (
                'https://jenkinsci-staging.saltstack.com/job/{branch}/job'
                '/{suite}/{build_number}/testReport/api/json'
            ).format(
                branch=branch,
                suite=suite,
                build_number=build_number,
            )
            log.info('Getting test report from %r', uri)
            resp = requests.get(
                uri,
                headers={'accept': 'application/json'},
                #auth=requests.auth.HTTPBasicAuth(user, password),
            )
            if resp.status_code != 200:
                log.warning('Bad status %r', resp.status_code)
                continue
            data = resp.json()
            for suite in data['suites']:
                for case in suite['cases']:
                    times[case['className']] += case['duration'] / 60
            total = 0
            for name, time in times.most_common(100):
                total += time
                print(f'{name:<70} {time:>7,.3f}')
            print('Total:', total/60, 'hrs')
            with open('times.csv', 'w') as f:
                for name, time in times.most_common(100):
                    f.write(f'{name}\t{time:.3f}\n')
            return


def builds(branch, suite, number_of_builds=1):
    uri = (
        'https://jenkinsci-staging.saltstack.com/job/{branch}/job'
        '/{suite}/api/json'
    ).format(
        branch=branch,
        suite=suite,
    )
    resp = requests.get(
        uri,
        headers={'accept': 'application/json'},
        #auth=requests.auth.HTTPBasicAuth(user, password),
    )
    log.debug('Fetching builds for branch: %s suite: %s uri: %s', branch, suite, uri)
    if resp.status_code != 200:
        log.error('Unable to fetch builds: %s %s %s %s', branch, suite, uri, resp.status_code)
        return
    for build in sorted(resp.json()['builds'], key=lambda x: x['number'], reverse=True):
        yield build['url']
#
#
#def test_report(branch, suite, build_number):
#    uri = (
#        'https://jenkinsci.saltstack.com/job/{branch}/job'
#        '/{suite}/{build_number}/testReport/api/json'
#    ).format(
#        branch=branch,
#        suite=suite,
#        build_number=build_number,
#    )
#    resp = requests.get(
#        uri,
#        headers={'accept': 'application/json'},
#        auth=requests.auth.HTTPBasicAuth(user, password))
#    if resp.status_code != 200:
#        return
#    testsuite = suite
#    data = resp.json()
#    for suite in data['suites']:
#        for case in suite['cases']:
#            test, _, klass = case['className'].rpartition('.')
#            if case['status'] not in ('PASSED', 'SKIPPED',):
#                uri = (
#                    'https://jenkinsci.saltstack.com/job/{branch}/job'
#                    '/{suite}/{build_number}/testReport/junit/{test}/'
#                    '{testclass}/{testcase}'
#                ).format(
#                    branch=branch,
#                    suite=testsuite,
#                    build_number=build_number,
#                    test=test,
#                    testclass=klass,
#                    testcase=case['name'],
#                )
#                yield case, uri
#
#
#def main():
#    test_failures = {}
#    suite_failures = {}
#    for job_url in all_jobs():
#        parts = job_url.split('/')
#        branch = parts[4]
#        suite = parts[6]
#        for url in builds(branch, suite, 1):
#            parts = url.split('/')
#            branch = parts[4]
#            suite = parts[6]
#            build_number = parts[7]
#            has_failures = False
#            for case, uri in test_report(branch, suite, build_number):
#                has_failures = True
#                full_name = '{}.{}'.format(case['className'], case['name'])
#                failure = TestFailure(
#                    full_name,
#                    branch,
#                    suite,
#                    case,
#                    uri=uri,
#                )
#                if full_name not in test_failures:
#                    test_failures[full_name] = {}
#                if branch not in test_failures[full_name]:
#                    test_failures[full_name][branch] = [failure]
#                else:
#                    test_failures[full_name][branch].append(failure)
#            if not has_failures:
#                if suite not in suite_failures:
#                    suite_failures[suite] = [branch]
#                else:
#                    suite_failures[suite].append(branch)
#            #print('\n')
#    for name in suite_failures:
#        print("Suite {} failed on {}".format(name, ', '.join(suite_failures[name])))
#    for name in test_failures:
#        print('*' * 80)
#        branches = []
#        for branch in test_failures[name]:
#            branches.append(
#                '{} failed {}'.format(
#                    branch, ', '.join(
#                        [
#                            f'[{str(x.suite)}]({x.uri})'
#                            for x in test_failures[name][branch]
#                        ]
#                    )
#                )
#            )
#        case = test_failures[name][branch][-1].case
#        print(template.format(
#            title=name,
#            branches='\n'.join(branches),
#            details=case['errorDetails'],
#            stacktrace=case['errorStackTrace'],
#        ))


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(message)s')
    do_it()
