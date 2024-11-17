# SPDX-License-Identifier: WTFPL
# SPDX-FileCopyrightText: 2024 Anna <cyber@sysrq.in>
# No warranty

"""
Personal advice utility for Gentoo package maintainers: Repology plugin
"""

import click
from click_aliases import ClickAliasedGroup

from find_work.core.cli.options import MainOptions
from find_work.core.cli.plugins import cli_hook_impl

import find_work.plugins.repology.cli as plugin_cli
from find_work.plugins.repology.options import RepologyOptions


@cli_hook_impl
def attach_base_command(group: ClickAliasedGroup) -> None:
    group.add_command(plugin_cli.repology, aliases=["rep", "r"])


@cli_hook_impl
def setup_base_command(options: MainOptions) -> None:
    if "repology" not in options.children:
        options.children["repology"] = RepologyOptions()


@cli_hook_impl
def get_command_by_name(command: str) -> click.Command | None:
    plug_name, cmd_name = command.split(":")[:2]
    if plug_name == "repology":
        match cmd_name:
            case "outdated":
                return plugin_cli.outdated
    return None
