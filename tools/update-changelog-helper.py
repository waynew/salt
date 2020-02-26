import git.util
import pathlib
import json
import quiz


def dump_data():
    auth = git.util.load_auth()
    schema = git.util.get_schema(auth=auth, url=git.util.GITHUB_GRAPHQL_API)

    # Man it will be nice when quiz supports spreads!
    _ = quiz.SELECTOR
    end_cursor = ""
    all_the_things = []
    while end_cursor is not None:
        search_kwargs = {
            "type": schema.SearchType.ISSUE,
            "first": 100,
            "query": "repo:saltstack/salt is:pr is:closed is:merged base:master created:>2019-01-01 sort:created-asc",
        }
        if end_cursor:
            search_kwargs["after"] = end_cursor
        # fmt: off
        query = schema.query[
            _
            .search(**search_kwargs)[
                _
                .pageInfo[
                    _
                    ('end_cursor').endCursor
                ]
                .edges[
                    _
                    .node
                ]
            ]
        ]
        x = quiz.InlineFragment(schema.PullRequest,
            quiz.SelectionSet()
                .number
                .url
                .title
                ('created_at').createdAt
                .state
                ('body').bodyText
                .author[
                    _
                    .login
                ]
        )
        # fmt: on
        query = str(query).replace("node", f"node {{{x.__gql__()}}}")
        results = quiz.execute(query, url=git.util.GITHUB_GRAPHQL_API, auth=auth)
        end_cursor = results["search"]["pageInfo"].get("end_cursor")
        all_the_things.extend(x["node"] for x in results["search"]["edges"])
        for edge in results["search"]["edges"][:1]:
            print(edge["node"]["number"])

    with open("/tmp/changelog_stuff", "w") as f:
        json.dump(all_the_things, f, indent=2)


def do_the_needful():
    changelog = pathlib.Path("~/programming/salt/CHANGELOG.md").expanduser().read_text()
    with open("/tmp/changelog_stuff") as f:
        data = json.load(f)
        for i, item in enumerate(data):
            num = item["number"]
            if f"#{num}" in changelog:
                print(f"#{num} already in changelog")
                continue
            print()
            header = f'Processing {i+1}/{len(data)} - {item["number"]} - {item["url"]}'
            header += "\n" + "=" * len(header)
            print(header)
            print(f'- [#{item["number"]}]({item["url"]}) - {item["title"]} - [@{item["author"]["login"]}](https://github.com/{item["author"]["login"]})')


if __name__ == "__main__":
    #dump_data()
    do_the_needful()
