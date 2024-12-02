# SPDX-License-Identifier: WTFPL
# SPDX-FileCopyrightText: 2024 Anna <cyber@sysrq.in>
# No warranty

"""
Implementation of CLI commands for the packages.gentoo.org plugin.
"""

import asyncio
from collections.abc import Set
from typing import Any

import click
from click_aliases import ClickAliasedGroup
from pydantic import TypeAdapter, validate_call

from find_work.core.cache import (
    read_raw_json_cache,
    write_raw_json_cache,
)
from find_work.core.cli.messages import Status, Result
from find_work.core.cli.options import MainOptions
from find_work.core.cli.widgets import ProgressDots
from find_work.core.types.results import PkgcheckResultsGroup


@validate_call
async def _stabilization(options: MainOptions) -> None:
    from find_work.plugins.pgo.internal import (
        collect_stable_requests,
        fetch_stabilization,
    )
    from find_work.plugins.pgo.types import StableRequest

    dots = ProgressDots(options.verbose)

    data: Set[StableRequest]
    with dots(Status.CACHE_READ):
        raw_data = read_raw_json_cache(options.breadcrumbs)
    if raw_data:
        with dots(Status.CACHE_LOAD):
            data = TypeAdapter(Set[StableRequest]).validate_json(raw_data)
    else:
        with dots("Fetching data from the Gentoo Packages website"):
            data = await fetch_stabilization(options)
        if len(data) == 0:
            # exit before writing empty cache
            return options.exit(Result.EMPTY_RESPONSE)
        with dots(Status.CACHE_WRITE):
            raw_json = TypeAdapter(Set[StableRequest]).dump_json(
                data, exclude_none=True  # type: ignore
            )
            write_raw_json_cache(raw_json, options.breadcrumbs)

    no_work = True
    with options.get_reporter_for(PkgcheckResultsGroup) as reporter:
        for result in collect_stable_requests(data, options):
            reporter.add_result(result)
            no_work = False

    if no_work:
        return options.exit(Result.NO_WORK)


@click.group(cls=ClickAliasedGroup,
             epilog="See `man find-work-pgo` for the full help.")
@click.pass_obj
def pgo(options: MainOptions, **kwargs: Any) -> None:
    """
    Use Gentoo Packages website to find work.
    """

    options.breadcrumbs.feed("pgo")


@pgo.command(aliases=["stabil", "s"])
@click.pass_context
def stabilization(ctx: click.Context, *, init_parent: bool = False) -> None:
    """
    Find stable requests.
    """

    options: MainOptions = ctx.obj
    if init_parent:
        ctx.invoke(pgo, indirect_call=True)

    options.breadcrumbs.feed("stabilization")

    asyncio.run(_stabilization(options))
