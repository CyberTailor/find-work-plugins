# SPDX-License-Identifier: WTFPL
# SPDX-FileCopyrightText: 2024 Anna <cyber@sysrq.in>
# No warranty

"""
pkgcheck subcommand options.
"""

from collections.abc import Sequence

from pydantic import Field

from find_work.core.cli.options import OptionsBase


class PkgcheckOptions(OptionsBase):
    """
    Options for pkgcheck subcommands.
    """

    #: Repository name or absolute path.
    repo: str = ""

    #: Class of the pkgcheck warning, e.g. DeprecatedEapi.
    keywords: list[str] = Field(default_factory=list)

    #: Message of the pkgcheck warning, e.g. 'uses deprecated EAPI 5'.
    message: str = ""

    @property
    def attr_order(self) -> Sequence[str]:
        return ["repo", "keywords", "message"]
