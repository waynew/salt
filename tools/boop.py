times = []
with open('/tmp/funtimes.tsv') as f:
    for line in f:
        data = line.split('\t')
        suite = data[-2]
        time = float(data[-1])
        times.append((time, suite))


times.sort()
THRESHOLD = 10
total = 0.0
count = 0
badcount = 0
suites = set()
badsuites = set()
for time in times:
    suite, *_ = time[1].rpartition('.')
    if total < THRESHOLD:
        if suite.startswith('unit.states') or suite.startswith('unit.modules') or suite.startswith('integration.states') or suite.startswith('integration.modules'):
            continue
        total += time[0]
        count += 1
        suites.add(suite)
    else:
        if not (suite.startswith('unit.states') or suite.startswith('unit.modules') or suite.startswith('integration.states') or suite.startswith('integration.modules')):
            badsuites.add(suite)

print(count, 'test suites in', total, 'minutes')
print(len(badsuites), 'Missing from "core" salt')
print('\n'.join(sorted(badsuites)))
#print('\n'.join(sorted(suites)))
