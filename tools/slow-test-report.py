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

Slow Test Report
================

This is a somewhat simple tool that will provide the top N slowest tests in
Salt's Jenkins environment.

Run it like this:

    python3 slow-test-report.py

And it will spit out the 10 slowest tests. Or run it like this:

    python3 slow-test-report.py 25

And it will spit out the 25 slowest tests. Output is on stderr,
so to save results just redirect to a file.
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

log = logging.getLogger("slow-test-report")

parser = argparse.ArgumentParser(
    description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
)
parser.add_argument("count", default=10, nargs="?", type=int)
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


async def collect_test_times():
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
        for comparison in asyncio.as_completed(tasks):
            test_name, results = await comparison
            test_class_results[test_name] = collections.Counter()
            if results is None:
                log.warning("No results for %r", test_name)
            else:
                for result in results:
                    class_name = result["className"]
                    test_class_results[test_name][class_name] += result["duration"]
        return test_class_results


def show_tsv_results(results, count):
    headers = ["Test Run", "Test Suite", "Duration"]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=headers, delimiter='\t')
    writer.writeheader()
    for test_run in results:
        for result in results[test_run].most_common(count):
            writer.writerow(
                {"Test Run": test_run, "Test Suite": result[0], "Duration": f"{result[1]:.2f}"}
            )
    output.seek(0)
    print(output.read())


def show_plain_results(results, count):
    for test_run in sorted(results):
        print(test_run)
        if not results[test_run]:
            print('\tUnable to find any test runs')
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
    test_times = loop.run_until_complete(collect_test_times())
    if args.plain or not any((args.plain, args.tsv)):
        show_plain_results(test_times, count=args.count)
    elif args.tsv:
        show_tsv_results(test_times, count=args.count)
