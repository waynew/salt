#!/usr/bin/env python3.7
import subprocess

branch_name = input("What branch? ")
build_name = input("What build name? ")
build_number = input("What build number? ")

url = f'https://jenkinsci.saltstack.com/job/{branch_name}/job/{build_name}/{build_number}/consoleText'
print('Pulling from', url)
subprocess.run([
    'curl',
    '-o',
    f'salt-{branch_name}-{build_name.replace("salt-","")}.{build_number}.log',
    url,
])
#salt-debian-8-py3.59.log https://jenkinsci.saltstack.com/job/neon/view/Python3/job/salt-debian-8-py3/59/consoleText
