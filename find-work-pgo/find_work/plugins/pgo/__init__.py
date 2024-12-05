# SPDX-License-Identifier: WTFPL
# SPDX-FileCopyrightText: 2024 Anna <cyber@sysrq.in>
# No warranty

"""
Personal advice utility for Gentoo package maintainers: packages.gentoo.org plugin
"""

import click
from click_aliases import ClickAliasedGroup

from find_work.core.cli.plugins import cli_hook_impl

import find_work.plugins.pgo.cli as plugin_cli


@cli_hook_impl
def attach_base_command(group: ClickAliasedGroup) -> None:
    group.add_command(plugin_cli.pgo, aliases=["p"])


@cli_hook_impl
def get_command_by_name(command: str) -> click.Command | None:
    plug_name, cmd_name = command.split(":")[:2]
    if plug_name == "pgo":
        match cmd_name:
            case "stabilization":
                return plugin_cli.stabilization
    return None
