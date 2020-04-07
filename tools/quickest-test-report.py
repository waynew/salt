# -*- coding: utf-8 -
"""
                                 ,_-''-_,
                 ,_-''-_,    ,_-'        '-_,
             ,_-'        +_-'                -,
         ,_-'            '-_,                ,+
     ,_-'                |   '-_,        ,_-' |
 ,_-'                ,_-'|       '-, ,_-'     |
 '-_,                '-_,|          |         |
 |   '-_,                '-_,       |         |
 |       '-_,                ',     |        ,+
 |           '-_,         ,_-'|     |    ,_-'
 |               '-_, ,_-'    | '-_,|,_-'|
 |                   |        |    ,_-'  |
 |                   |        |,_-'      |
 |                   |                   |
 |                   |                   |
 |                   |                   |
 '-_,                |                ,_-'
     '-_,            |            ,_-'
         '-_,        |        ,_-'
             '-_,    |    ,_-'
                 '-_,|,_-'

Quickest Test Report
====================

This is a somewhat simple tool that will provide a report of the quickest
test suites in Salt's Jenkins environment.

Run it like this:

    python3 quickest-test-report.py

And it will spit out all the test suites (files) that can run within 10
minutes.

Or for 25 minutes, you can run like:

    python3 quickest-test-report.py 25

And it will spit out the tests that can run within 25 minutes. Output is on
stderr, so to save results just redirect to a file.

Another way to run it:

    python3 quickest-test-report.py --comprehensive

And it will produce a list of test suites as well as classes/tests within each
file.

Or:

    python3 quickest-test-report.py 5 --comprehensive --test-limit 0.1

This will produce a comprehensive report, but skip any test that takes longer
than 0.1 seconds to run.

"""

import aiohttp
import argparse
import asyncio
import collections
import csv
import io
import logging
import os
import sys
import tempfile

import jenkins_utils

log = logging.getLogger("quickest-test-report")

parser = argparse.ArgumentParser(
    description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
)
parser.add_argument(
    "time", default=10, nargs="?", type=int, help="Time, in minutes, to filter tests."
)
group = parser.add_mutually_exclusive_group()
group.add_argument(
    "--plain",
    help="Display report in plain text, suitable for the command line.",
    action="store_true",
)
group.add_argument(
    "--tsv",
    help="Display report as tab-separated values, suitable for piping to a file, or copy-pasting to a spreadsheet.",
    action="store_true",
    default=False,
)
parser.add_argument(
    "--logfile",
    default=os.path.join(tempfile.gettempdir(), "test-report.log"),
    type=argparse.FileType("w"),
)
parser.add_argument(
    "--comprehensive",
    action="store_true",
    help="Produce a comprehensive report, with individual tests and times.",
)
parser.add_argument("--keep-skipped", action="store_true", default=False, help="Keep skipped tests.")
parser.add_argument(
    "--test-limit",
    type=float,
    help="Time, in seconds - ignore individual tests that take longer than this number of seconds.",
)


async def collect_test_times(keep_skipped):
    async with aiohttp.ClientSession() as session:
        urls = await jenkins_utils.get_suite_urls(
            session=session, branch="Master Branch Jobs", jenkins_env="jenkinsci"
        )
        log.debug("Checking %r URLs", urls)

        tasks = set(
            asyncio.create_task(
                jenkins_utils.get_most_recent_test_results(session=session, url=url)
            )
            for url in urls
        )
        test_class_results = {}
        test_results = {}
        for comparison in asyncio.as_completed(tasks):
            test_name, results = await comparison
            test_class_results[test_name] = collections.Counter()
            test_results[test_name] = {}
            if results is None:
                log.warning("No results for %r", test_name)
            else:
                for result in results:
                    class_name = result["className"]
                    test_case_name = result["name"]
                    skipped = result["skipped"]
                    if not skipped or (skipped and keep_skipped):
                        test_results[test_name][
                            f"{class_name}.{test_case_name}"
                        ] = result["duration"]
                        test_class_results[test_name][class_name] += result["duration"]
        return test_class_results, test_results


def show_tsv_results(*, test_results, time, comprehensive, test_limit):
    headers = ["Test Run", "Test Suite", "Duration"]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=headers, delimiter="\t")
    writer.writeheader()
    for test_run in results:
        for result in results[test_run].most_common(count):
            writer.writerow(
                {
                    "Test Run": test_run,
                    "Test Suite": result[0],
                    "Duration": f"{result[1]:.2f}",
                }
            )
    output.seek(0)
    print(output.read())


def show_plain_results(*, test_results, time, comprehensive, test_limit):
    grand_total = 0
    bad_counter = collections.Counter()
    for pipeline_name in sorted(test_results):
        #print(pipeline_name)
        r = [
            (test_results[pipeline_name][test_name], test_name)
            for test_name in test_results[pipeline_name]
        ]
        r.sort()
        total_test_seconds = 0.0
        time_limit_seconds = 60*time  # 60s * time - time is in minutes
        count = 0
        integration_count = 0
        for result in r:
            test_time, test_name = result
            if test_limit is None or test_time < test_limit:
                if total_test_seconds + test_time >= time_limit_seconds:
                    #break
                    bad_counter[test_name] += 1
                else:
                    count += 1
                    grand_total += 1
                    total_test_seconds += test_time
                    if test_name.startswith('integration.'):
                        integration_count += 1
                    #log.debug(f'\t{test_name}{test_time}')
            else:
                bad_counter[test_name] += 1
        print(f"{pipeline_name}\t{count}\t{time_limit_seconds}\t{total_test_seconds}\t{count}/{len(r)}={count/len(r) if r else '?'}%")
        #print(f'\tTotal:  {count} Integration count: {integration_count} tests {total_test_seconds:.2f}s')

    #import pprint; pprint.pprint(bad_counter.most_common(20))
    #print(grand_total)
    return
    if False:
        last_test_name = None
        for test_name in test_results[pipeline_name]:
            split_name = test_name.split(".")
            if last_test_name != split_name[:-1]:
                last_test_name = split_name[:-1]
                tabs = "\t" * len(last_test_name)
                print(tabs, ".".join(last_test_name))
            last_test_name = test_name.split()
            result = test_results[pipeline_name][test_name]
            if test_limit is None or result < test_limit:
                print(tabs + "\t", split_name[-1])
    return
    for test_run in sorted(results):
        print(test_run)
        if not results[test_run]:
            print("\tUnable to find any test runs")
            continue
        width = max(len(test) for test in results[test_run])
        for test, duration in results[test_run].most_common(count):
            print(f"\t{test:<{width}} {duration:>8.2f}")


if __name__ == "__main__":
    args = parser.parse_args()
    log = logging.getLogger()
    log.handlers.clear()
    sh = logging.StreamHandler(args.logfile)
    sh.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(message)s"))
    log.addHandler(sh)
    log.setLevel(logging.DEBUG)
    print("Logging to", args.logfile.name, file=sys.stderr)
    loop = asyncio.get_event_loop()
    test_times, individual_test_times = loop.run_until_complete(
        collect_test_times(args.keep_skipped)
    )
    if args.plain or not any((args.plain, args.tsv)):
        show_plain_results(
            test_results=individual_test_times,
            time=args.time,
            comprehensive=args.comprehensive,
            test_limit=args.test_limit,
        )
    elif args.tsv:
        show_tsv_results(
            test_results=individual_test_times,
            time=args.time,
            comprehensive=args.comprehensive,
            test_limit=args.test_limit,
        )
