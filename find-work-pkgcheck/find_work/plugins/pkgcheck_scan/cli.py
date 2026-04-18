# SPDX-License-Identifier: WTFPL
# SPDX-FileCopyrightText: 2024-2026 Anna <cyber@sysrq.in>
# No warranty

"""
Implementation of CLI commands for the pkgcheck plugin.
"""

from contextlib import redirect_stdout
from io import StringIO
from typing import Any

import click
from click_aliases import ClickAliasedGroup
from pydantic import TypeAdapter

from find_work.core.cache import (
    read_raw_json_cache,
    write_raw_json_cache,
)
from find_work.core.cli.messages import Result, Status
from find_work.core.cli.options import MainOptions
from find_work.core.cli.widgets import ProgressDots
from find_work.core.types.results import PkgcheckResultsGroup

from find_work.plugins.pkgcheck_scan.options import PkgcheckOptions


@click.group(cls=ClickAliasedGroup,
             epilog="See `man find-work-pkgcheck` for the full help.")
@click.option("-M", "--message", metavar="LIST",
              help="Warning message to search for.")
@click.option("-j", "--jobs", metavar="JOBS", type=int, default=0,
              help="Number of parallel jobs for pkgcheck.")
@click.option("-k", "--keywords", metavar="LIST",
              help="Keywords to scan for.")
@click.option("-r", "--repo", metavar="REPO", required=True,
              help="Repository name or absolute path.")
@click.pass_obj
def pkgcheck(options: MainOptions, message: str | None, jobs: int,
             keywords: str | None, repo: str, *,
             indirect_call: bool = False) -> None:
    """
    Use pkgcheck to find work.
    """

    options.breadcrumbs.feed("pkgcheck")

    plugin_options = PkgcheckOptions.model_validate(
        options.children["pkgcheck"]
    )

    if not indirect_call:
        plugin_options.repo = repo
        plugin_options.keywords = list(filter(None, (keywords or "").split(",")))
        plugin_options.message = message or ""
        plugin_options.jobs = jobs

    for key in plugin_options.attr_order:
        options.breadcrumbs.feed_option(key, plugin_options[key])


@pkgcheck.command(aliases=["s"])
@click.pass_obj
def scan(options: MainOptions, **kwargs: Any) -> None:
    from find_work.plugins.pkgcheck_scan.internal import (
        do_pkgcheck_scan,
        get_packages_for_maintainer,
    )

    options.breadcrumbs.feed("scan")

    dots = ProgressDots(options.verbose)
    pkg_list: list[str] = []
    if options.maintainer:
        with dots(Status.CACHE_READ):
            raw_pkg_list = read_raw_json_cache(options.breadcrumbs)
        if raw_pkg_list:
            with dots(Status.CACHE_LOAD):
                pkg_list = TypeAdapter(list[str]).validate_json(raw_pkg_list)
        else:
            with dots("Preparing a list of packages for this scan"):
                pkg_list = get_packages_for_maintainer(options)
            if len(pkg_list) == 0:
                return options.exit(Result.EMPTY_RESPONSE)
            with dots(Status.CACHE_WRITE):
                adapter: TypeAdapter[list[str]] = TypeAdapter(list[str])
                raw_json = adapter.dump_json(pkg_list, exclude_none=True)
                write_raw_json_cache(raw_json, options.breadcrumbs)

    with dots("Scouring the neighborhood"):
        # this works because pkgcheck.base.ProgressManager checks
        # that sys.stdout is a TTY
        with redirect_stdout(StringIO()):
            data = do_pkgcheck_scan(options, pkg_list)

    no_work = True
    with options.get_reporter_for(PkgcheckResultsGroup) as reporter:
        for package, results in data.items():
            reporter.add_result(
                PkgcheckResultsGroup(atom=package, results=results)
            )
            no_work = False

    if no_work:
        return options.exit(Result.NO_WORK)
    return None
