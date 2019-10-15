import logging

log = logging.getLogger(__name__)


def get_last_build(result):
    """
    Return the url for the most recent likely build from a Jenkins result.
    Default to last successful build, then stable, then just last completed
    build.

    If we can't find *any* build, return None.
    """
    keys = ("lastSuccessfulBuild", "lastStableBuild", "lastCompletedBuild")
    for key in keys:
        try:
            return result[key]["url"].rstrip("/") + "/testReport/api/json"
        except KeyError:
            log.error("No %r build for %r", key, result.get("name", "unknown build"))
        except TypeError:
            log.error("No %r build for %r", key, result.get("name", "unknown build"))
    return None


async def get_suite_urls(*, session, branch, jenkins_env):
    url = f"https://{jenkins_env}.saltstack.com/view/{branch}/api/json"
    headers = {"Accept": "application/json"}
    log.debug("Requesting from %r", url)
    async with session.get(url, headers=headers) as resp:
        if resp.status != 200:
            log.error(
                "Failed getting results with status code %r:\n%s",
                resp.status,
                await resp.text(),
            )
        else:
            result = await resp.json()
            log.debug("Found %r suites", len(result["jobs"]))
            urls = [job["url"].rstrip("/") + "/api/json" for job in result["jobs"]]
            # Cloud build times aren't available to the public.
            # Doc builds are irrelevant.
            for ignored_suite in ("cloud", "docs"):
                urls = [url for url in urls if ignored_suite not in url]
            return urls


async def get_most_recent_test_results(*, session, url):
    headers = {"Accept": "application/json"}
    async with session.get(url, headers=headers) as resp:
        if resp.status != 200:
            log.error(
                "Failed getting results with status code %r:\n%s",
                resp.status,
                await resp.text(),
            )
        else:
            result = await resp.json()
            name = result["fullDisplayName"]
            last_build = get_last_build(result)
            if last_build is None:
                return name, None
            return name, await get_build_results(session=session, url=last_build)


async def get_build_results(*, session, url):
    headers = {"Accept": "application/json"}
    log.error("Getting build results from %r", url)
    async with session.get(url, headers=headers) as resp:
        if resp.status != 200:
            log.error("Failed to get build results from %r", url)
        else:
            result = await resp.json()
            cases = []
            for suite in result["suites"]:
                for case in suite["cases"]:
                    cases.append(case)
            log.debug("Got %r cases", len(cases))
            return cases
