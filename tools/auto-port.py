import os
import subprocess
import sys

import quiz

import git.util


class Blarp(quiz.utils.ValueObject):
    __fields__ = [("content", str, "Awesome")]

    def __gql__(self):
        return "howdy howdy howdy"


class Boop(quiz.SelectionSet):
    def __init__(self, raw_stuff):
        self.__raw = raw_stuff
        self.__selections__ = [Blarp("herp")]

    def __gql__(self):
        return f"{{{self.__raw}}}"


def do_it():  # Shia LeBeouf
    auth = git.util.load_auth()
    schema = git.util.get_schema(auth=auth, url=git.util.GITHUB_GRAPHQL_API)
    owner = "saltstack"
    reponame = "salt"

    _ = quiz.SELECTOR
    x = quiz.InlineFragment(schema.PullRequest, quiz.SelectionSet().number)
    end_cursor = ""
    pr_numbers = []
    while end_cursor is not None:
        card_kwargs = {"first": 100}
        if end_cursor:
            card_kwargs["after"] = end_cursor
        # fmt: off
        query = schema.query[
            _
            .repository(owner=owner, name=reponame)[
                _
                .project(number=5)[
                    _
                    .columns(first=1)[
                        _
                        .nodes[
                            _
                            .cards(**card_kwargs)[
                                _
                                ('page_info').pageInfo[
                                    _
                                    ('end_cursor').endCursor
                                ]
                                .edges[
                                    _
                                    .node[
                                        _
                                        .content
                                    ]
                                ]
                            ]
                        ]
                    ]
                ]
            ]
        ]
        # fmt: on
        query = str(query).replace("content", f"content\n{{{x.__gql__()}}}")
        result = quiz.execute(query, git.util.GITHUB_GRAPHQL_API, auth=auth)
        end_cursor = result["repository"]["project"]["columns"]["nodes"][0]["cards"][
            "page_info"
        ].get("end_cursor")

        for node in result["repository"]["project"]["columns"]["nodes"][0]["cards"][
            "edges"
        ]:
            pr_number = node["node"]["content"]["number"]
            pr_numbers.append(pr_number)

    with open("/tmp/failures.txt", "w") as f:
        for num in sorted(pr_numbers):
            print("Fetching hashes for", num)
            os.chdir("/Users/wwerner/util/tools")
            output = subprocess.run(
                [sys.executable, "commits-in-pr.py", str(num)], capture_output=True
            )
            hashes = output.stdout.decode().splitlines()
            try:
                if not hashes:
                    raise Exception("No hashes?")
                os.chdir("/Users/wwerner/programming/salt")
                subprocess.run(["git", "cherry-pick", "--abort"])
                r = subprocess.run(["git", "checkout", "salt/master"])
                r = subprocess.run(["git", "checkout", "-B", f"master-port/{num}"])
                r = subprocess.run(["git", "fetch", "salt", f"refs/pull/{num}/head"])
                cmd = ["git", "cherry-pick"] + hashes
                print("running", cmd)
                r = subprocess.run(cmd)
            except:
                subprocess.run(["git", "reset", "--hard", "HEAD"])
                print(f"Failed {num} hashes - {hashes!r}", file=f)
                f.flush()

            if os.path.exists("/tmp/abort"):
                print("aborting!")
                exit(1)


if __name__ == "__main__":
    do_it()
