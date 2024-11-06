# SPDX-License-Identifier: WTFPL
# SPDX-FileCopyrightText: 2024 Anna <cyber@sysrq.in>
# No warranty

"""
Implementation of CLI commands for the pkgcheck plugin.
"""

from typing import Any

import click
from click_aliases import ClickAliasedGroup

from find_work.cli.messages import Result
from find_work.cli.options import MainOptions
from find_work.cli.widgets import ProgressDots

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
        data = do_pkgcheck_scan(options)

    if len(data) == 0:
        return options.exit(Result.NO_WORK)

    for package, results in data.items():
        options.echo()
        options.secho(package, fg="cyan", bold=True)
        for item in results:
            options.echo("\t", nl=False)
            options.secho(item.name, fg=item.color, nl=False)
            options.echo(": ", nl=False)
            options.echo(item.desc)

    return None
