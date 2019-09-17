#!/usr/bin/env python3
"""
Test times from Jenkins
"""

import argparse
import asyncio
import csv
import logging
import os
import pathlib

import aiohttp

import requests
import requests.auth

from collections import Counter

log = logging.getLogger("test-times")

JENKINS_ENV = os.environ.get("JENKINS_ENV", "jenkinsci-staging")
JENKINS_A_ENV = os.environ.get(
    "JENKINS_A_ENV", os.environ.get("JENKINS_ENV", "jenkinsci")
)
JENKINS_B_ENV = os.environ.get("JENKINS_B_ENV", JENKINS_ENV)
BRANCH_A_FORMAT = (
    f"https://{JENKINS_A_ENV}.saltstack.com/job/{{branch}}/view/All/api/json"
)
BRANCH_B_FORMAT = (
    f"https://{JENKINS_B_ENV}.saltstack.com/job/{{branch}}/view/All/api/json"
)
TEST_A_BUILD_FORMAT = (
    f"https://{JENKINS_A_ENV}.saltstack.com/job/{{branch}}/job/{{suite}}/api/json"
)
TEST_B_BUILD_FORMAT = (
    f"https://{JENKINS_B_ENV}.saltstack.com/job/{{branch}}/job/{{suite}}/api/json"
)
TEST_A_REPORT_FORMAT = (
    "https://{JENKINS_A_ENV}.saltstack.com/job/{{branch}}/job"
    "/{suite}/{build_number}/testReport/api/json"
)
TEST_A_REPORT_FORMAT = (
    "https://{JENKINS_B_ENV}.saltstack.com/job/{{branch}}/job"
    "/{suite}/{build_number}/testReport/api/json"
)


def make_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "suite",
        help="Test suite to use, such as salt-debian-9-py3 - see individual builds on https://jenkinsci.saltstack.com - use ALL for all suites on the branch, but beware this could take a while.",
    )
    parser.add_argument(
        "src_branch", help="Source branch - the main test times to consider"
    )
    parser.add_argument(
        "cmp_branch", help="Comparison branch - test times will be source-comparison"
    )
    parser.add_argument(
        "--src-env", help="Jenkins environment for src branch", default="jenkinsci"
    )
    parser.add_argument(
        "--cmp-env", help="Jenkins environment for cmp branch", default="jenkinsci"
    )
    return parser


def all_jobs(branches):
    for branch in branches:
        uri = ("https://jenkinsci.saltstack.com/job/{branch}/view/All/api/json").format(
            branch=branch
        )
        log.debug("Fetching builds for branch:%s url: %s", branch, uri)
        resp = requests.get(
            uri,
            headers={"accept": "application/json"},
            # auth=requests.auth.HTTPBasicAuth(user, password),
        )
        data = resp.json()
        for job in data["jobs"]:
            if job["color"] == "red":
                yield job["url"]

    uri = (
        "https://jenkinsci-staging.saltstack.com/job/{branch}/job" "/{suite}/api/json"
    ).format(branch=branch, suite=suite)
    resp = requests.get(
        uri,
        headers={"accept": "application/json"},
        # auth=requests.auth.HTTPBasicAuth(user, password),
    )
    log.debug("Fetching builds for branch: %s suite: %s uri: %s", branch, suite, uri)
    if resp.status_code != 200:
        log.error(
            "Unable to fetch builds: %s %s %s %s", branch, suite, uri, resp.status_code
        )
        return
    for build in sorted(resp.json()["builds"], key=lambda x: x["number"], reverse=True):
        yield build["url"]


def test_results(env, branch, suite, number=None):
    uri = f"https://{env}.saltstack.com/job/{branch}/job/{suite}/api/json"
    r = requests.get(uri)
    if r.status_code != 200:
        raise Exception(
            "Unable to fetch builds: %s %s %s %s %s",
            env,
            branch,
            suite,
            uri,
            r.status_code,
        )
    for build in sorted(r.json()["builds"], key=lambda x: x["number"], reverse=True):
        build_number = build["number"]
        if number and number != build_number:
            continue
        uri = (
            f"https://{env}.saltstack.com/job/{branch}/job/{suite}/{build_number}"
            "/testReport/api/json"
        )
        r = requests.get(uri)
        if r.status_code != 200:
            log.warning("No test results found at %r", uri)
        else:
            for suite in r.json()["suites"]:
                for case in suite["cases"]:
                    yield case


def do_it():
    count = 0
    suite = "salt-debian-9-py3"
    suite = "salt-debian-9-py3"
    a = {"env": "jenkinsci", "branch": "neon", "suite": suite}
    b = {"env": "jenkinsci", "branch": "2019.2.1", "suite": suite}
    a_results = Counter()
    b_results = Counter()
    for result in test_results(**a):
        a_results[result["className"]] += (
            result["duration"] / 60
        )  # duration is in seconds

    for result in test_results(**b):
        b_results[result["className"]] += (
            result["duration"] / 60
        )  # duration is in seconds

    print(len(b_results))

    comparisons = {}
    for name in a_results:
        comparisons[name] = {"a": a_results[name], "b": b_results[name]}

    #  A env              A branch  A duration  B duration   B env               B branch
    #  jenkinsci-staging  neon      0.000       41.658       jenkinsci-staging   neon
    #  jenkinsci-staging  neon      0.000       27.883       jenkinsci           neon

    print(
        f'{"Test Name":<85} {"A env":<18} {"A branch":<10} {"A duration":<10} {"B duration":<10} {"B env":<18} {"B branch":<10}'
    )
    a_total = b_total = 0
    for name, duration in a_results.most_common(100):
        a_duration = a_results[name]
        if name.startswith("tests.") and not b_results[name]:
            name = name.partition(".")[-1]
        b_duration = b_results[name]
        a_total += a_duration
        b_total += b_duration
        print(
            f"{name:<85} {a['env']:<18} {a['branch']:<10} {a_duration:>10,.3f} {b_duration:>10,.3f} {b['env']:<18} {b['branch']:<10}"
        )

    print(f"A total: {a_total:4.3f} / B total: {b_total:4.3f}")
    print("*" * 50)
    print()
    print(
        f'{"Test Name":<85} {"A env":<18} {"A branch":<10} {"A duration":<10} {"B duration":<10} {"B env":<18} {"B branch":<10}'
    )
    a_total = b_total = 0
    for name, duration in b_results.most_common(100):
        b_duration = b_results[name]
        if not name.startswith("tests.") and not a_results[name]:
            name = "tests." + name
        a_duration = a_results[name]
        a_total += a_duration
        b_total += b_duration
        print(
            f"{name:<85} {a['env']:<18} {a['branch']:<10} {a_duration:>10,.3f} {b_duration:>10,.3f} {b['env']:<18} {b['branch']:<10}"
        )
    print(f"A total: {a_total:4.3f} / B total: {b_total:4.3f}")

    diffs = Counter()
    for name in a_results:
        a_duration = a_results[name]
        if name.startswith("tests.") and not b_results[name]:
            name = name.partition(".")[-1]
        b_duration = b_results[name]
        diff = a_duration - b_duration
        diffs[name] = diff

    for name, duration in diffs.most_common(10):
        print(f"{duration:>7,.3f} {name}")

    print("*" * 50, end="\n" * 2)
    for name, duration in list(reversed(diffs.most_common()))[:10]:
        print(f"{duration:>7,.3f} {name}")


def builds(branch, suite, number_of_builds=1):
    uri = (
        "https://jenkinsci-staging.saltstack.com/job/{branch}/job" "/{suite}/api/json"
    ).format(branch=branch, suite=suite)
    resp = requests.get(uri, headers={"accept": "application/json"})
    log.debug("Fetching builds for branch: %s suite: %s uri: %s", branch, suite, uri)
    if resp.status_code != 200:
        log.error(
            "Unable to fetch builds: %s %s %s %s", branch, suite, uri, resp.status_code
        )
        return
    for build in sorted(resp.json()["builds"], key=lambda x: x["number"], reverse=True):
        yield build["url"]


def compare_test_times(*, src, cmp):
    """
    Compare two Jenkins test report results
    """
    test_times = {}
    for case in src:
        test_times[case["className"]] = {
            "src_duration": 0,
            "src_status": case["status"],
            "cmp_duration": None,
            "cmp_status": "MISSING",
            "diff": None,
        }
        test_times[case["className"]]["src_duration"] += case["duration"]
    for case in cmp:
        name = case["className"]
        try:
            test_times[name]["cmp_status"] = case["status"]
            test_times[name]["cmp_duration"] = test_times[name].get("cmp_duration") or 0
        except KeyError:
            test_times[name] = {
                "src_duration": None,
                "src_status": "MISSING",
                "diff": None,
            }
        test_times[name]["cmp_duration"] = (
            test_times[name].get("cmp_duration", 0) + case["duration"]
        )
        try:
            test_times[name]["diff"] = (
                test_times[name]["src_duration"] - test_times[name]["cmp_duration"]
            )
        except TypeError:
            pass  # No comparison to make here
    log.debug("Test times compared for %r test cases", len(test_times))
    return test_times


def get_last_build(result):
    """
    Return the url for the most recent likely build from a Jenkins result.
    Default to last successful build, then stable, then just last completed
    build.

    If we can't find *any* build, return None.
    """
    keys = ("lastSuccessfulBuild", "lastStableBuild", "lastCompletedBuild")
    for key in keys:
        try:
            return result[key]["url"].rstrip("/") + "/testReport/api/json"
        except KeyError:
            log.error("No %r build for %r", key, result.get("name", "unknown build"))
        except TypeError:
            log.error("No %r build for %r", key, result.get("name", "unknown build"))
    return None


async def get_build_results(*, session, uri):
    headers = {"Accept": "application/json"}
    log.debug("Getting build results from %r", uri)
    async with session.get(uri, headers=headers) as response:
        if response.status != 200:
            log.error("Failed to get build results from %r", uri)
        else:
            result = await response.json()
            cases = []
            for suite in result["suites"]:
                for case in suite["cases"]:
                    cases.append(case)
            log.debug("Got %r cases", len(cases))
            return cases


async def get_test_comparison(
    *, session, suite, src_branch, cmp_branch, src_env, cmp_env
):
    log.debug("comparing le times for %r", suite)
    src_uri = f"https://{src_env}.saltstack.com/job/{src_branch}/job/{suite}/api/json"
    cmp_uri = f"https://{cmp_env}.saltstack.com/job/{cmp_branch}/job/{suite}/api/json"
    headers = {"Accept": "application/json"}
    log.debug("Requesting suite status for %r", src_uri)
    async with session.get(src_uri, headers=headers) as response:
        if response.status == 200:
            result = await response.json()
            last_build = get_last_build(result)
            if last_build is None:
                return suite, None
            src_build_results = await get_build_results(session=session, uri=last_build)
        else:
            log.error("%r failed, %s", suite, await response.text())
            return suite, None
    async with session.get(cmp_uri, headers=headers) as response:
        if response.status == 200:
            result = await response.json()
            last_build = get_last_build(result)
            if last_build is None:
                return suite, None
            cmp_build_results = await get_build_results(session=session, uri=last_build)
        else:
            log.error("%r failed, %s", suite, await response.text())
            return suite, None
    if not all((src_build_results, cmp_build_results)):
        nones = []
        if src_build_results is None:
            nones.append("src")

        if cmp_build_results is None:
            nones.append("cmp")

        # If nones raises an IndexError then something has gone horribly wrong here.
        log.error(
            "%r failed to compare because %s was None",
            suite,
            "both" if len(nones) == 2 else nones[0],
        )
        return suite, None
    comparison = compare_test_times(src=src_build_results, cmp=cmp_build_results)
    log.debug("%r times were compared", suite)
    return suite, comparison


async def get_suite_list(*, session, branch, env):
    uri = f"https://{env}.saltstack.com/job/{branch}/api/json"
    headers = {"Accept": "application/json"}
    log.debug("Requesting from %r", uri)
    async with session.get(uri, headers=headers) as response:
        if response.status == 200:
            result = await response.json()
            log.debug("Found %r suites", len(result["jobs"]))
            jobs = [job["name"] for job in result["jobs"]]
            # Need to ignore cloud build times because they aren't
            # generally available to the public.
            for ignored_suite in ("cloud", "docs"):
                jobs = [job for job in jobs if ignored_suite not in job]
            return jobs
        else:
            log.error("erg... something failed", await response.text(), response.status)
            return []


async def do_it_async(*, suite, src_branch, cmp_branch, src_env, cmp_env):
    async with aiohttp.ClientSession() as session:
        if suite == "ALL":
            suites = await get_suite_list(
                session=session, branch=src_branch, env=src_env
            )
        else:
            suites = [suite]
        tasks = set(
            asyncio.create_task(
                get_test_comparison(
                    session=session,
                    suite=suite,
                    src_branch=src_branch,
                    cmp_branch=cmp_branch,
                    src_env=src_env,
                    cmp_env=cmp_env,
                )
            )
            for suite in suites
        )
        output_dir = pathlib.Path("/tmp/test-time-comparisons")
        output_dir.mkdir(parents=True, exist_ok=True)
        for comparison in asyncio.as_completed(tasks):
            this_suite, result = await comparison
            suite_file = output_dir / (this_suite + ".tsv")
            if result is None:
                suite_file.write_text("Unable to compare builds on these branches")
                continue
            with suite_file.open("w") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=[
                        "suite",
                        "test",
                        "src_branch",
                        "cmp_branch",
                        "src_status",
                        "cmp_status",
                        "src_duration",
                        "cmp_duration",
                        "diff",
                    ],
                    delimiter="\t",
                )
                writer.writerow(
                    {
                        "suite": "Build Name",
                        "test": "Test Name",
                        "src_branch": "Source Branch",
                        "cmp_branch": "Comparison Branch",
                        "src_status": "Source Test Result",
                        "cmp_status": "Comparison Test Result",
                        "src_duration": "Source Test Duration",
                        "cmp_duration": "Comparison Test Duration",
                        "diff": "Source duration - Comparison Duration",
                    }
                )
                for test_name in result:
                    r = result[test_name]
                    r.update(
                        {
                            "suite": this_suite,
                            "test": test_name,
                            "src_branch": src_branch,
                            "cmp_branch": cmp_branch,
                        }
                    )
                    writer.writerow(r)
            log.info("Wrote test results to %s", suite_file)


if __name__ == "__main__":
    parser = make_parser()
    f = logging.Formatter("%(asctime)s:%(levelname)s:%(name)s:%(message)s")
    h = logging.FileHandler("/tmp/util.log")
    h.setFormatter(f)
    log.addHandler(h)
    log.setLevel(logging.DEBUG)
    args = parser.parse_args()
    log.debug(str(args))
    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        do_it_async(
            suite=args.suite,
            src_branch=args.src_branch,
            src_env=args.src_env,
            cmp_branch=args.cmp_branch,
            cmp_env=args.cmp_env,
        )
    )
