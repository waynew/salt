import subprocess
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def original_revision():
    original_rev = subprocess.check_output(['git', 'rev-parse', 'HEAD']).strip()
    try:
        yield
    finally:
        subprocess.run(['git', 'checkout', original_rev])


with open('/tmp/merge_commits.txt') as f:
    commits = [line.strip() for line in f]

times_by_commit = {}
with original_revision():
    pwd = Path().resolve()
    for i, commit in enumerate(reversed(commits)):
        print(commit, f'{i}/{len(commits)}')
        cmd = [
            'git',
            'checkout',
            commit,
        ]
        subprocess.run(cmd)
        cmd = [
            'docker',
            'run',
            '--rm',
            '-it',
            '-v',
            f'{pwd}:/testing',
            'waynew/salt-sprints',
            'python3',
            '/testing/tests/runtests.py',
            '--run-destructive',
            '-n',
            'integration.states.test_file.FileTest.test_comment',
        ]
        op = subprocess.run(cmd, capture_output=True)
        last_test = None
        test_seconds = None
        times = {}
        for line in op.stdout.decode():
            if line.startswith('Starting '):
                last_test = line.strip()
            elif line.startswith('Ran ') and 'tests in' in line:
                test_seconds = float(line[:-1].rsplit(None, 1)[-1])
                times[last_test] = test_seconds
        times_by_commit[commit] = times or 'Failed'
        with open('times_by_commit.log', 'a') as f:
            print(commit, times, file=f)
    with open('times_by_commit.txt', 'w') as f:
        for commit in times_by_commit:
            print(commit, times_by_commit[commit], file=f)
