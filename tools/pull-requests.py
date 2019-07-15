#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import subprocess
import tempfile

from pathlib import Path


SALT_ACTIVE_BRANCHES = [
    'develop',
    'neon',  # Release
    '2019.2',  # Release-1
    '2018.3',  # Release-1
]


BANNER = '''
      ___           ___                                 
     /\__\         /\  \                                
    /:/ _/_       /::\  \                       ___     
   /:/ /\  \     /:/\:\  \                     /\__\    
  /:/ /::\  \   /:/ /::\  \   ___     ___     /:/  /    
 /:/_/:/\:\__\ /:/_/:/\:\__\ /\  \   /\__\   /:/__/     
 \:\/:/ /:/  / \:\/:/  \/__/ \:\  \ /:/  /  /::\  \     
  \::/ /:/  /   \::/__/       \:\  /:/  /  /:/\:\  \    
   \/_/:/  /     \:\  \        \:\/:/  /   \/__\:\  \   
     /:/  /       \:\__\        \::/  /         \:\__\  
     \/__/         \/__/         \/__/           \/__/  

Welcome to the SaltStack Pull Request Helper.

This tool should make life easier for you when submitting PRs to SaltStack.
Select the branch you were working off of, and the branch(es) you want your
code in - then all that's left is copy and pasting a couple of times: pushing
the branches to your fork, and the text of your PR.

Report any bugs at https://github.com/saltstack/salt/issues
'''





def show_active_branches(branches=SALT_ACTIVE_BRANCHES):
    print('Active Branches:')
    for i, branch in enumerate(branches, start=1):
        print(f'\t{i}. {branch}')


def get_root_branch():
    show_active_branches()
    branch = input('Where did you branch from? ').strip()
    if branch in SALT_ACTIVE_BRANCHES:
        root_branch = branch
    else:
        try:
            i = int(branch) - 1
        except ValueError:
            print(f'ERROR: {branch!r} not a valid branch name.')
            print()
            root_branch = get_root_branch()
        else:
            if 0 <= i < len(SALT_ACTIVE_BRANCHES):
                root_branch = SALT_ACTIVE_BRANCHES[i]
            else:
                print(f'ERROR: {i+1} not a valid branch number.')
                print()
                root_branch = get_root_branch()

    return root_branch


def get_alt_branches(root_branch):
    all_alts = [br for br in SALT_ACTIVE_BRANCHES if br != root_branch]
    show_active_branches(all_alts)
    branches = input(
        f'What other branches should we target? (default {", ".join(all_alts)}): '
    )
    selected_alts = set()
    for branch in (br.strip() for br in branches.split(',')):
        if branch in all_alts:
            selected_alts.add(branch)
        else:
            try:
                i = int(branch) - 1
            except ValueError:
                print(f'ERROR: {branch!r} not a valid branch name.')
                print()
                selected_alts.update(get_alt_branches(root_branch))
            else:
                if 0 <= i < len(all_alts):
                    selected_alts.add(all_alts[i])
                else:
                    print(f'ERROR: {i+1} not a valid branch number.')
                    print()
                    selected_alts.update(get_alt_branches(root_branch))
    return selected_alts


def fetch_remotes(branches):
    '''
    Run git fetch on the provided ``branches``, using the configured
    saltstack remote. If one is not found, fallback to https, with
    confirmation.
    '''
    remotes = subprocess.check_output(['git', 'remote', '-v']).decode()
    saltstack_remote = 'https://github.com/saltstack/salt.git'
    for remote in remotes.split('\n'):
        if 'saltstack/salt' in remote and remote.strip().endswith('(fetch)'):
            saltstack_remote = remote.split(None, maxsplit=1)[0]
            break
    else:
        confirm = input(f'No saltstack remote found, OK to run `git remote add salt {saltstack_remote}`? [Y/n]: ')
        if confirm.lower() not in ('', 'y', 'yes'):
            sys.exit('Aborted - no salt remote found')

    for branch in branches:
        subprocess.run(['git', 'fetch', saltstack_remote, branch])

    return saltstack_remote


def do_it():  # Shia LeBeouf!
    print(BANNER)
    root_branch = get_root_branch()
    alt_branches = get_alt_branches(root_branch)
    cur_branch = (
        subprocess.check_output(['git', 'symbolic-ref', '--short', 'HEAD'])
        .decode()
        .strip()
    )
    new_branches = [cur_branch + '-' + br for br in alt_branches]
    print('About to fetch remotes and create the following branches:')
    for branch in new_branches:
        print(f'\t{branch}')
    confirm = input('Is this OK? [Y/n]: ')
    if confirm.lower() not in ('', 'y', 'yes', 'okay', 'si', 'da', 'oui'):
        print('Aborted!')
        return
    saltstack_remote = fetch_remotes(alt_branches)
    with tempfile.NamedTemporaryFile() as d:
        patchfile = Path(d.name)
        output = subprocess.check_output(
            ['git', 'format-patch', root_branch, '--stdout']
        )
        patchfile.write_bytes(output)

        for alt_branch, new_branch in zip(alt_branches, new_branches):
            subprocess.run(['git', 'checkout', f'{saltstack_remote}/{alt_branch}'])
            subprocess.run(['git', 'checkout', '-b', new_branch])
            print('Applying patch')
            subprocess.run(['git', 'am', str(patchfile.resolve())])
    print('Assuming your fork is named origin, run the following:')
    for branch in new_branches:
        print(f'\tgit push origin {branch}')


if __name__ == '__main__':
    try:
        do_it()
    except KeyboardInterrupt:
        print()
        print('^C caught, aborting!')
