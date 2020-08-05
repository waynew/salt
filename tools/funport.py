import csv
import sqlite3
from collections import defaultdict, Counter


class Result:
    def __init__(self, pipeline, test, duration):
        self.pipeline = pipeline
        self.name = test
        self.duration = float(duration)


class PipeLine:
    def __init__(self, name=""):
        self.name = name
        self.results = []

    @property
    def hours(self):
        total_seconds = sum(r.duration for r in self.results)
        return total_seconds / 60


all_the_tests = defaultdict(PipeLine)
# with open('/tmp/all-times.csv') as f:
with open("/tmp/all-times-unskipped.csv") as f:
    reader = csv.DictReader(f)
    for row in reader:
        all_the_tests[row["Pipeline"]].name = row["Pipeline"]
        all_the_tests[row["Pipeline"]].results.append(
            Result(
                pipeline=row["Pipeline"],
                test=row["Test Name"],
                duration=float(row["Duration"]),
            )
        )


by_times = {
    0.01: Counter(),
    0.1: Counter(),
    1: Counter(),
    10: Counter(),
    30: Counter(),
    60: Counter(),
    120: Counter(),
    "rest": Counter(),
}
by_pipeline_by_times = {name: defaultdict(Counter) for name in all_the_tests}
times = (0.01, 0.1, 1, 10, 30, 60, 120)
for name in sorted(all_the_tests, key=lambda x: all_the_tests[x].hours):
    pipeline = all_the_tests[name]
    # [print(pipeline.name, pipeline.hours)
    for result in pipeline.results:
        for time in times:
            if result.duration < time:
                by_times[time][result.name] += 1
                by_pipeline_by_times[pipeline.name][time][result.name] += 1
                break
        else:
            by_times["rest"][result.name] += 1
            by_pipeline_by_times[pipeline.name]["rest"][result.name] += 1


# for time in times + ('rest', ):
#    print('Number of tests under', time, 'seconds')
#    #print('\t', *by_times[time].most_common()[-1])
#    #print('\t', *by_times[time].most_common()[-2])
#    print('\t', len(by_times[time]))


# for name in sorted(all_the_tests):
#    timecounts = [len(by_pipeline_by_times[name][time]) for time in times + ('rest',)]
#    print(name, '\t'.join(str(x) for x in timecounts), sep='\t')


def do_one():
    all_tests_max_min = defaultdict(dict)
    all_test_names = set()
    tests_under_1s_at_least_once = set()
    for name in all_the_tests:
        for result in all_the_tests[name].results:
            all_tests_max_min[result.name]["max"] = max(
                all_tests_max_min[result.name].get("max", 0), result.duration
            )
            all_tests_max_min[result.name]["min"] = min(
                all_tests_max_min[result.name].get("min", 500000), result.duration
            )
            all_test_names.add(result.name)
            if result.duration < 1:
                tests_under_1s_at_least_once.add(result.name)

    tests_never_under_1s = all_test_names - tests_under_1s_at_least_once
    for test in tests_never_under_1s:
        print(
            test,
            all_tests_max_min[test]["max"],
            all_tests_max_min[test]["min"],
            sep="\t",
        )


def do_two():
    win_test_times = defaultdict(dict)
    all_win_test_names = set()
    win_tests_under_1s_at_least_once = set()
    win_plat_time = {'time': 0, 'count': 0}

    mac_test_times = defaultdict(dict)
    all_mac_test_names = set()
    mac_tests_under_1s_at_least_once = set()
    mac_plat_time = {'time': 0, 'count': 0}

    linux_test_times = defaultdict(dict)
    all_linux_test_names = set()
    linux_tests_under_1s_at_least_once = set()
    linux_plat_time = {'time': 0, 'count': 0}

    for name in all_the_tests:
        pipeline = all_the_tests[name]

        if "windows" in pipeline.name.lower():
            test_names = all_win_test_names
            test_times = win_test_times
            tests_under_1s = win_tests_under_1s_at_least_once
            plat_time = win_plat_time
        elif "macos" in pipeline.name.lower():
            test_names = all_mac_test_names
            test_times = mac_test_times
            tests_under_1s = mac_tests_under_1s_at_least_once
            plat_time = mac_plat_time
        else:
            test_names = all_linux_test_names
            test_times = linux_test_times
            tests_under_1s = linux_tests_under_1s_at_least_once
            plat_time = linux_plat_time

        plat_time['count'] += 1
        for result in pipeline.results:
            test_names.add(result.name)
            test_times[result.name]["max"] = max(
                test_times[result.name].get("max", 0), result.duration
            )
            test_times[result.name]["min"] = min(
                test_times[result.name].get("min", 500000), result.duration
            )
            if result.duration < 1:
                tests_under_1s.add(result.name)
                plat_time['time'] += result.duration

    print(f'Win <1s total time {win_plat_time["time"]/win_plat_time["count"]/60:.2f}m')
    print(f'Mac <1s total time {mac_plat_time["time"]/mac_plat_time["count"]/60:.2f}m')
    print(f'Nux <1s total time {linux_plat_time["time"]/linux_plat_time["count"]/60:.2f}m')
    return
    win_test_never_under_1s = all_win_test_names - win_tests_under_1s_at_least_once
    mac_test_never_under_1s = all_mac_test_names - mac_tests_under_1s_at_least_once
    linux_test_never_under_1s = (
        all_linux_test_names - linux_tests_under_1s_at_least_once
    )
    print(
        "test name",
        "win max",
        "win min",
        "mac max",
        "mac min",
        "linux max",
        "linux min",
        sep="\t",
    )
    all_tests_never_under_1s = set()
    all_tests_never_under_1s.update(win_test_never_under_1s)
    all_tests_never_under_1s.update(mac_test_never_under_1s)
    all_tests_never_under_1s.update(linux_test_never_under_1s)
    for test in all_tests_never_under_1s:
        wintest, mactest, linuxtest = (
            win_test_times.get(test, {}),
            mac_test_times.get(test, {}),
            linux_test_times.get(test, {}),
        )
        print(
            test,
            wintest.get("max", ""),
            wintest.get("min", ""),
            mactest.get("max", ""),
            mactest.get("min", ""),
            linuxtest.get("max", ""),
            linuxtest.get("min", ""),
            sep="\t",
        )


if __name__ == "__main__":
    do_two()
