"""
Pulls down the latest documentation changes from Jenkins and launches the docs
in your web browser so you can easily review changes.
"""
import argparse
import io
import os
import requests
import tarfile
import tempfile
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler

# TODO: it would be wicked awesome if this could yoink the changed files from
# the PR and use that to launch the changed pages.

# We'll see how long it takes me to do the other part, though.

JENKINS_URL = "https://jenkinsci.saltstack.com/job/pr-docs/job/PR-{pr_number}/lastSuccessfulBuild/artifact/doc/html-archive.tar.xz"

class MyError(Exception): pass
class ArchiveNotFoundError(MyError): pass



def make_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pr_number", type=int, help="GitHub Pull Request Number")

    return parser


def get_archive(*, pr_number):
    url = JENKINS_URL.format(pr_number=pr_number)
    print('Getting latest docs ...')
    r = requests.get(url)
    if r.status_code != 200:
        raise ArchiveNotFoundError(f'Attempted archive URL {url}')
    return r.content


def serve_archive(*, archive):
    data = io.BytesIO(archive)
    with tarfile.open(mode='r:xz', fileobj=data) as tar:
        with tempfile.TemporaryDirectory() as tempdir:
            original = os.path.abspath(os.path.curdir)
            try:
                tar.extractall(tempdir)
                os.chdir(tempdir)
                os.chdir('_build/html')
                server = HTTPServer(('', 8000), SimpleHTTPRequestHandler)
                webbrowser.open('http://localhost:8000/contents.html')
                print('Serving!')
                server.serve_forever()
            except KeyboardInterrupt:
                print('\nByeeee')
            finally:
                os.chdir(original)
                print('Cleaning up')


def do_it():  # Shia LeBeouf!
    parser = make_parser()
    args = parser.parse_args()
    try:
        archive = get_archive(pr_number=args.pr_number)
    except ArchiveNotFoundError as e:
        print('Unable to retrieve archive;', e)
        exit()
    serve_archive(archive=archive)
    print('Okay, done!')


if __name__ == '__main__':
    do_it()
