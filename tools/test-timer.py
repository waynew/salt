import subprocess


first_commit = 'salt/2019.2.1'   # git log start..end will not include this
last_commit = 'rebase-bad-neon'

print(f'''
Salt Test Timer
===============

This is a gnarly bit of fun designed to run over tests from one
commit to another. Currently the commits are hard-coded, so
change {__file__} if you want to do something different.
''')

print(f'Running from {first_commit} to {last_commit}.')
try:
    cont = input('Continue? [Y/n]: ')
    if cont.strip().lower() in ('', 'y', 'yes', 'si', 'ja', 'oui', 'da'):
        commits = [subprocess.check_output(['git', 'rev-parse', first_commit])]
        commits.extend(subprocess.check_output(['git', 'log', '--format', '%H', f'{first_commit}..{last_commit}']).decode().split('\n'))
        print(commits)
    else:
        print('Aborted')
except KeyboardInterrupt:
    print('\n^C - Aborting!')
