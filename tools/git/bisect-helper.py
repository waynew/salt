#!/usr/bin/env python3.7
'''
Author: Wayne Werner <wwerner@saltstack.com>

This is not a full-fledged tool yet, but it should be mildly helpful when
trying to do some sorts of advanced bisect(s). Rather than manually having
to specify whether a revision is good or bad, you can simply add rules to
return GitStatus.good or GitStatus.bad.

Each commit hash in the bisect tree will be stored in /tmp/revisions.log.

Should be invoked like so:

    git bisect start
    git bisect good REVISION
    git bisect bad REVISION
    git bisect run ./tools/bisect-helper.py

For more information about bisects, see the git book at
https://git-scm.com/docs/git-bisect/2.1.0

Requires Python 3.4 or newer, with a default shebang using 3.7.
'''
import subprocess
import sys
from enum import IntEnum


class GitStatus(IntEnum):
    good = 0
    bad = 1

    def toggle(self):
        return GitStatus.good if self is self.bad else GitStatus.bad


#op = [line.strip() for line in subprocess.check_output(['git', 'bisect', 'log']).decode().split('\n')]
git_status = GitStatus.good

try:
    with open('/tmp/last_stat', 'r') as f:
        last_stat = f.read().strip().lower()
        git_status  = GitStatus[last_stat].toggle()
except (FileNotFoundError, KeyError):
    pass

with open('/tmp/last_stat', 'w') as f:
    f.write(git_status.name)

#for line in op:
#    if not line.startswith('#'):
#        try:
#            last_stat = line.split()[2]
#        except IndexError:
#            continue

print('Exit with:', git_status)

#if False and sys.argv[1] == 'swap':
#    exit_code = not exit_code


with open('/tmp/revisions.log', 'ab') as f:
    f.write(subprocess.check_output(['git', 'rev-parse', 'HEAD']))

sys.exit(git_status)
