# SPDX-License-Identifier: WTFPL
# SPDX-FileCopyrightText: 2024 Anna <cyber@sysrq.in>
# No warranty

"""
Personal advice utility for Gentoo package maintainers: pkgcheck plugin
"""

import logging

import click
from click_aliases import ClickAliasedGroup

from find_work.core.cli.options import MainOptions
from find_work.core.cli.plugins import cli_hook_impl

import find_work.plugins.pkgcheck_scan.cli as plugin_cli
from find_work.plugins.pkgcheck_scan.options import PkgcheckOptions


@cli_hook_impl
def attach_base_command(group: ClickAliasedGroup) -> None:
    group.add_command(plugin_cli.pkgcheck, aliases=["chk", "c"])


@cli_hook_impl
def setup_base_command(options: MainOptions) -> None:
    if "pkgcheck" not in options.children:
        options.children["pkgcheck"] = PkgcheckOptions()

    # silence pkgcore
    pkgcore_logger = logging.getLogger("pkgcore")
    pkgcore_logger.setLevel(logging.CRITICAL)


@cli_hook_impl
def get_command_by_name(command: str) -> click.Command | None:
    plug_name, cmd_name = command.split(":")[:2]
    if plug_name == "pkgcheck":
        match cmd_name:
            case "scan":
                return plugin_cli.scan
    return None
