# SPDX-License-Identifier: WTFPL
# SPDX-FileCopyrightText: 2024 Anna <cyber@sysrq.in>
# No warranty

"""
Implementation of CLI commands for the pkgcheck plugin.
"""

from contextlib import redirect_stdout
from io import StringIO
from typing import Any

import click
from click_aliases import ClickAliasedGroup

from find_work.core.cli.messages import Result
from find_work.core.cli.options import MainOptions
from find_work.core.cli.widgets import ProgressDots
from find_work.core.types.results import PkgcheckResultsGroup

from find_work.plugins.pkgcheck_scan.options import PkgcheckOptions


@click.group(cls=ClickAliasedGroup)
@click.option("-M", "--message", metavar="LIST",
              help="Warning message to search for.")
@click.option("-k", "--keywords", metavar="LIST",
              help="Keywords to scan for.")
@click.option("-r", "--repo", metavar="REPO", required=True,
              help="Repository name or absolute path.")
@click.pass_obj
def pkgcheck(options: MainOptions, message: str | None, keywords: str | None,
             repo: str, *, indirect_call: bool = False) -> None:
    """
    Use pkgcheck to find work.

    See `man find-work-pkgcheck` for the full help.
    """

    plugin_options = PkgcheckOptions.model_validate(
        options.children["pkgcheck"]
    )

    if not indirect_call:
        plugin_options.repo = repo
        plugin_options.keywords = (keywords or "").split(",")
        plugin_options.message = message or ""


@pkgcheck.command(aliases=["s"])
@click.pass_obj
def scan(options: MainOptions, **kwargs: Any) -> None:
    from find_work.plugins.pkgcheck_scan.internal import do_pkgcheck_scan

    dots = ProgressDots(options.verbose)

    with dots("Scouring the neighborhood"):
        # this works because pkgcheck.base.ProgressManager checks
        # that sys.stdout is a TTY
        with redirect_stdout(StringIO()):
            data = do_pkgcheck_scan(options)

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
