import argparse
import asyncio
import csv
import json
import logging
import pathlib


log = logging.getLogger("pr-test-checker")
log.addHandler(logging.FileHandler("/tmp/pr-test-checker.log"))
log.setLevel(logging.DEBUG)

try:
    import aiohttp
except ImportError:
    import sys

    sys.exit(
        "aiohttp failed to import. Try `{sys.executable} -m pip install --user aiohttp` first"
    )


def directory(path):
    p = pathlib.Path(path).expanduser().resolve()
    if not p.exists():
        raise Exception(f"Unable to find {p!s}")
    return p


parser = argparse.ArgumentParser()
parser.add_argument("file", type=argparse.FileType("r"))
parser.add_argument("--github-api-key", type=argparse.FileType("r"))
parser.add_argument("--dump-dir", type=directory)


async def get_changes(*, pr, session, api_token):
    url = f"https://api.github.com/repos/saltstack/salt/pulls/{pr}/files"
    log.debug("Checking %r", url)
    headers = {"Authorization": f"token {api_token}"}
    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            return await response.json()
        else:
            return None


async def get_pr_title_and_text(*, pr, session, api_token):
    url = f"https://api.github.com/repos/saltstack/salt/pulls/{pr}"
    log.debug("Checking %r", url)
    headers = {"Authorization": f"token {api_token}"}
    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            result = await response.json()
            return result["title"], result["body"]
        else:
            return None, None


def is_doc_only_change(files_changed):
    has_doc_change = any(filename.startswith('doc/') for filename in files_changed)
    has_other_changes = any(filename.startswith('salt/') or filename.startswith('tests/') for filename in files_changed)
    return has_doc_change and not has_other_changes


async def do_it(*, file, api_token, dump_dir):
    reader = csv.DictReader(file)
    ordered_prs = [row["pr"] for row in reader]
    has_tests = {}
    has_doc_changes = {}
    async with aiohttp.ClientSession() as session:
        prlen = len(ordered_prs)
        for count, pr in enumerate(ordered_prs, start=1):
            log.debug('%r/%r - %0.2f%%', count, prlen, count/prlen)
            changes = await get_changes(pr=pr, session=session, api_token=api_token)
            if changes:
                files_changed = [change["filename"] for change in changes]
                has_tests[pr] = any(
                    filename.startswith("tests/") for filename in files_changed
                )
                has_doc_changes[pr] = is_doc_only_change(files_changed)
            else:
                has_tests[pr] = False
                has_doc_changes[pr] = False
            pr_title, pr_text = await get_pr_title_and_text(
                pr=pr, session=session, api_token=api_token
            )
            if dump_dir is not None:
                fpath = dump_dir / (str(pr) + ".json")
                with fpath.open("a+") as f:
                    f.seek(0)
                    try:
                        data = json.load(f)
                    except Exception as e:
                        log.warning("Failed to load json %s", e)
                        data = {}
                    f.seek(0)
                    data["changes"] = changes
                    data["title"] = pr_title
                    data["text"] = pr_text
                    json.dump(data, f, indent=4)
                    f.truncate()

    with open("/tmp/prs.txt", "w") as f:
        for pr in ordered_prs:
            msg = f'{"YES" if has_doc_changes[pr] else "NO"}\t{"YES" if has_tests[pr] else "NO"}\t=IF(INDIRECT(ADDRESS(ROW(), 2))="{pr}", "OK", "OOPS")'
            print(msg, file=f)
            print(msg)


if __name__ == "__main__":
    args = parser.parse_args()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        do_it(
            file=args.file,
            api_token=args.github_api_key.read().strip(),
            dump_dir=args.dump_dir,
        )
    )
