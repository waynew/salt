import csv
import re
from pathlib import Path
from collections import Counter

slowest_test_times = Counter()

with open('/tmp/all-times-unskipped.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        name = row['Test Name']
        time = float(row['Duration'])
        slowest_test_times[name] = max(slowest_test_times[name], time)


def make_markers(slow_time):
    if slow_time < 1:
        return ['@skipIf(True, "FASTTEST skip")']
    return []
    times = (
        (0.01, '@pytest.mark.slow_0_01'),
        (0.1, '@pytest.mark.slow_0_1'),
        (1, '@pytest.mark.slow_1'),
        (10, '@pytest.mark.slow_10'),
        (30, '@pytest.mark.slow_30'),
        (60, '@pytest.mark.slow_60'),
    )
    markers = set()
    for time, marker in times:
        if slow_time > time:
            markers.add(marker)
    return list(sorted(markers))


for name in sorted(set(slowest_test_times), key=lambda x: slowest_test_times[x]):
    time = slowest_test_times[name]
    root, _, test_name = name.rpartition('.')
    root, _, klass = root.rpartition('.')
    p = Path('/Users/wwerner/programming/salt/tests/', *(root.split('.'))).with_suffix('.py')
    try:
        data = p.read_text()
        markers = make_markers(time)
        if markers:
            pat = re.compile(rf'([^\S\n]+)def {test_name}\(')
            result = re.search(pat, data)
            if result:
                indent = result.group(1)
                assert len(markers) < 7
                to_write = '\n'.join(indent+marker for marker in markers)+'\n'+result.group(0)
                change = re.sub(pat, to_write, data)
                #if not re.search('\nimport pytest', change):
                if not re.search('\nfrom tests.support.unit import skipIf', change):
                    change = change.split('\n')
                    for i, line in enumerate(change):
                        if line.startswith('from __future__ import'):
                            #change.insert(i+1, 'import pytest')
                            change.insert(i+1, 'from tests.support.unit import skipIf')
                            change = '\n'.join(change)
                            break
                    else:
                        #change = 'import pytest\n'+change
                        change = 'from tests.support.unit import skipIf\n'+change
                p.write_text(change)
    except FileNotFoundError:
        print(f'{name} not found at {p}')


#print(result, repr(result.groups()[0]), 'xxx')
#print(name)
#print(p, klass, test_name)
#print(make_markers(time), time)
