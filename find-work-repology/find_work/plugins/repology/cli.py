# SPDX-License-Identifier: WTFPL
# SPDX-FileCopyrightText: 2024 Anna <cyber@sysrq.in>
# No warranty

"""
Implementation of CLI commands for the Repology plugin.
"""

import asyncio

import click
import repology_client.exceptions
from click_aliases import ClickAliasedGroup
from pydantic import TypeAdapter, validate_call

from find_work.cache import (
    read_raw_json_cache,
    write_raw_json_cache,
)
from find_work.cli.messages import Status, Result
from find_work.cli.options import MainOptions
from find_work.cli.widgets import ProgressDots
from find_work.types import VersionPart

from find_work.plugins.repology.internal import (
    ProjectsMapping,
    collect_version_bumps,
    fetch_outdated,
)
from find_work.plugins.repology.options import (
    OutdatedCmdOptions,
    RepologyOptions,
)


@validate_call
async def _outdated(options: MainOptions) -> None:
    plugin_options = RepologyOptions.model_validate(
        options.children["repology"]
    )
    cmd_options = OutdatedCmdOptions.model_validate(
        plugin_options.children["outdated"]
    )
    dots = ProgressDots(options.verbose)

    with dots(Status.CACHE_READ):
        raw_data = read_raw_json_cache(options.breadcrumbs)
    if raw_data:
        with dots(Status.CACHE_LOAD):
            data = TypeAdapter(ProjectsMapping).validate_json(raw_data)
    else:
        try:
            with dots("Fetching data from Repology API"):
                data = await fetch_outdated(options)
        except repology_client.exceptions.EmptyResponse:
            return options.exit(Result.EMPTY_RESPONSE)
        with dots(Status.CACHE_WRITE):
            raw_json = TypeAdapter(ProjectsMapping).dump_json(
                data, exclude_none=True
            )
            write_raw_json_cache(raw_json, options.breadcrumbs)

    no_work = True
    for bump in collect_version_bumps(data.values(), options):
        if (
            cmd_options.version_part is None
            or bump.changed(cmd_options.version_part)
        ):
            options.echo(bump.atom + " ", nl=False)
            options.secho(bump.old_version, fg="red", nl=False)
            options.echo(" → ", nl=False)
            options.secho(bump.new_version, fg="green")
            no_work = False

    if no_work:
        return options.exit(Result.NO_WORK)


@click.group(cls=ClickAliasedGroup)
@click.option("-r", "--repo", metavar="NAME", required=True,
              help="Repository name on Repology.")
@click.pass_obj
def repology(options: MainOptions, repo: str = "", *,
             indirect_call: bool = False) -> None:
    """
    Use Repology to find work.
    """

    options.breadcrumbs.feed("repology")

    plugin_options = RepologyOptions.model_validate(
        options.children["repology"]
    )

    if not indirect_call:
        plugin_options.repo = repo

    for key in plugin_options.attr_order:
        options.breadcrumbs.feed_option(key, plugin_options[key])


@repology.command(aliases=["out", "o"])
@click.option("-F", "--filter", "version_part",
              type=click.Choice(["major", "minor", "patch"]),
              help="Version part filter.")
@click.pass_context
def outdated(ctx: click.Context, version_part: VersionPart | None = None, *,
             init_parent: bool = False) -> None:
    """
    Find outdated packages.
    """

    options: MainOptions = ctx.obj
    if init_parent:
        ctx.invoke(repology, indirect_call=True)

    options.breadcrumbs.feed("outdated")

    plugin_options = RepologyOptions.model_validate(
        options.children["repology"]
    )
    cmd_options = plugin_options.children["outdated"] = OutdatedCmdOptions()
    cmd_options.version_part = version_part

    asyncio.run(_outdated(options))