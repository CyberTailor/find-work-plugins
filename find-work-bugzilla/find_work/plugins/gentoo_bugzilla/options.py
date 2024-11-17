# SPDX-License-Identifier: WTFPL
# SPDX-FileCopyrightText: 2024 Anna <cyber@sysrq.in>
# No warranty

"""
Bugzilla subcommand options.
"""

from collections.abc import Sequence

from find_work.core.cli.options import OptionsBase


class BugzillaOptions(OptionsBase):
    """
    Options for Bugzilla subcommands.
    """

    # Product name.
    product: str = ""

    # Component name.
    component: str = ""

    # Bug summary.
    short_desc: str = ""

    # Sort by date last modified or by ID.
    chronological_sort: bool = False

    @property
    def attr_order(self) -> Sequence[str]:
        return ["chronological_sort", "short_desc", "product", "component"]
