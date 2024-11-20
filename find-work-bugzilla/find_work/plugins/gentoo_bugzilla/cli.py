# SPDX-License-Identifier: WTFPL
# SPDX-FileCopyrightText: 2024 Anna <cyber@sysrq.in>
# No warranty

"""
Implementation of CLI commands for the Bugzilla plugin.
"""

from typing import Any

import click
from click_aliases import ClickAliasedGroup
from pydantic import validate_call

from find_work.core.cache import (
    read_raw_json_cache,
    write_raw_json_cache,
)
from find_work.core.cli.messages import Status, Result
from find_work.core.cli.options import MainOptions
from find_work.core.cli.widgets import ProgressDots
from find_work.core.types.results import BugView

from find_work.plugins.gentoo_bugzilla.options import BugzillaOptions


@validate_call
def _list_bugs(options: MainOptions, **filters: Any) -> None:
    from find_work.plugins.gentoo_bugzilla.internal import (
        bugs_from_raw_json,
        bugs_to_raw_json,
        collect_bugs,
        fetch_bugs,
    )

    dots = ProgressDots(options.verbose)

    with dots(Status.CACHE_READ):
        raw_data = read_raw_json_cache(options.breadcrumbs)
    if raw_data:
        with dots(Status.CACHE_LOAD):
            data = bugs_from_raw_json(raw_data)
    else:
        with dots("Fetching data from Bugzilla API"):
            data = fetch_bugs(options, **filters)
        if len(data) == 0:
            return options.exit(Result.EMPTY_RESPONSE)
        with dots(Status.CACHE_WRITE):
            raw_json = bugs_to_raw_json(data)
            write_raw_json_cache(raw_json, options.breadcrumbs)

    no_work = True
    with options.get_reporter_for(BugView) as reporter:
        for bug in collect_bugs(data, options):
            reporter.add_result(bug)
            no_work = False

    if no_work:
        return options.exit(Result.NO_WORK)
    return None


@click.group(cls=ClickAliasedGroup)
@click.option("-Q", "--query",
              help="Search terms.")
@click.option("-c", "--component", metavar="NAME",
              help="Component name on Bugzilla.")
@click.option("-p", "--product", metavar="NAME",
              help="Product name on Bugzilla.")
@click.option("-t", "--time", is_flag=True,
              help="Sort bugs by time last modified.")
@click.pass_obj
def bugzilla(options: MainOptions, component: str | None = None,
             product: str | None = None, query: str | None = None,
             time: bool = False, *, indirect_call: bool = False) -> None:
    """
    Use Bugzilla to find work.

    See `man find-work-bugzilla` for the full help.
    """

    options.breadcrumbs.feed("bugzilla")

    plugin_options = BugzillaOptions.model_validate(
        options.children["bugzilla"]
    )

    if not indirect_call:
        plugin_options.chronological_sort = time
        plugin_options.short_desc = query or ""
        plugin_options.product = product or ""
        plugin_options.component = component or ""

    for key in plugin_options.attr_order:
        options.breadcrumbs.feed_option(key, plugin_options[key])


@bugzilla.command("list", aliases=["ls", "l"])
@click.pass_context
def ls(ctx: click.Context, *, init_parent: bool = False) -> None:
    """
    List bugs on Bugzilla.
    """

    options: MainOptions = ctx.obj
    if init_parent:
        ctx.invoke(bugzilla, indirect_call=True)

    options.breadcrumbs.feed("list")

    _list_bugs(options)
