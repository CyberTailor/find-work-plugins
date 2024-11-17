# SPDX-License-Identifier: WTFPL
# SPDX-FileCopyrightText: 2024 Anna <cyber@sysrq.in>
# No warranty

"""
Personal advice utility for Gentoo package maintainers: Bugzilla plugin
"""

import click
from click_aliases import ClickAliasedGroup

from find_work.core.cli.options import MainOptions
from find_work.core.cli.plugins import cli_hook_impl

import find_work.plugins.gentoo_bugzilla.cli as plugin_cli
from find_work.plugins.gentoo_bugzilla.options import BugzillaOptions


@cli_hook_impl
def attach_base_command(group: ClickAliasedGroup) -> None:
    group.add_command(plugin_cli.bugzilla, aliases=["bug", "b"])


@cli_hook_impl
def setup_base_command(options: MainOptions) -> None:
    if "bugzilla" not in options.children:
        options.children["bugzilla"] = BugzillaOptions()


@cli_hook_impl
def get_command_by_name(command: str) -> click.Command | None:
    plug_name, cmd_name = command.split(":")[:2]
    if plug_name == "bugzilla":
        match cmd_name:
            case "list":
                return plugin_cli.ls
    return None
