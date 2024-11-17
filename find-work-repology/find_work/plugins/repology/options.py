# SPDX-License-Identifier: WTFPL
# SPDX-FileCopyrightText: 2024 Anna <cyber@sysrq.in>
# No warranty

"""
Repology subcommand options.
"""

from collections.abc import Sequence

from find_work.core.cli.options import OptionsBase
from find_work.core.types import VersionPart


class OutdatedCmdOptions(OptionsBase):
    """
    Options for ``outdated`` command.
    """

    #: Version part filter.
    version_part: VersionPart | None = None

    @property
    def attr_order(self) -> Sequence[str]:
        return tuple()


class RepologyOptions(OptionsBase):
    """
    Options for Repology subcommands.
    """

    #: Repository name.
    repo: str = ""

    @property
    def attr_order(self) -> Sequence[str]:
        return ["repo"]
