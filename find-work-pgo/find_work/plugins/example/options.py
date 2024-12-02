# SPDX-License-Identifier: WTFPL
# SPDX-FileCopyrightText: 2024 Anna <cyber@sysrq.in>
# No warranty

"""
Example subcommand options.
"""

from collections.abc import Sequence

from find_work.core.cli.options import OptionsBase


class ExampleOptions(OptionsBase):
    """
    Options for example subcommands.
    """

    #: Repository name.
    repo: str = ""

    @property
    def attr_order(self) -> Sequence[str]:
        return ["repo"]
