# SPDX-License-Identifier: WTFPL
# SPDX-FileCopyrightText: 2024 Anna <cyber@sysrq.in>
# No warranty

"""
Implementation of CLI commands for the example plugin.
"""

import click
from click_aliases import ClickAliasedGroup

from find_work.core.cache import (
    read_raw_json_cache,
    write_raw_json_cache,
)
from find_work.core.cli.messages import Status, Result
from find_work.core.cli.options import MainOptions
from find_work.core.cli.widgets import ProgressDots

from find_work.plugins.example.options import ExampleOptions


def _ls(options: MainOptions) -> None:
    dots = ProgressDots(options.verbose)

    with dots(Status.CACHE_READ):
        raw_data = read_raw_json_cache(options.breadcrumbs)
    if raw_data:
        with dots(Status.CACHE_LOAD):
            data = ...
    else:
        with dots("Fetching data from nowhere"):
            data = ...
        if len(data) == 0:
            # exit before writing empty cache
            return options.exit(Result.EMPTY_RESPONSE)
        with dots(Status.CACHE_WRITE):
            raw_json = ...
            write_raw_json_cache(raw_json, options.breadcrumbs)

    no_work = True
    with options.get_reporter_for(...) as reporter:
        for result in range(10):
            reporter.add_result(result)
            no_work = False

    if no_work:
        return options.exit(Result.NO_WORK)
    return None


@click.group(cls=ClickAliasedGroup,
             epilog="See `man find-work-example` for the full help.")
@click.option("-r", "--repo", metavar="NAME", required=True,
              help="Repository name.")
@click.pass_obj
def example(options: MainOptions, repo: str = "", *,
            indirect_call: bool = False) -> None:
    """
    Use nothing to find work.
    """

    options.breadcrumbs.feed("example")

    plugin_options = ExampleOptions.model_validate(
        options.children["example"]
    )

    if not indirect_call:
        plugin_options.repo = repo

    for key in plugin_options.attr_order:
        options.breadcrumbs.feed_option(key, plugin_options[key])


@example.command(aliases=["ls", "l"])
@click.pass_context
def ls(ctx: click.Context, *, init_parent: bool = False) -> None:
    """
    List something.
    """

    options: MainOptions = ctx.obj
    if init_parent:
        ctx.invoke(example, indirect_call=True)

    options.breadcrumbs.feed("list")

    _ls(options)
