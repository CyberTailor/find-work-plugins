# SPDX-License-Identifier: WTFPL
# SPDX-FileCopyrightText: 2024 Anna <cyber@sysrq.in>
# No warranty

"""
Internal type definitions for Gentoo Packages GraphQL API, implemented as
Pydantic models.
"""

from pydantic import BaseModel, ConfigDict, Field

from find_work.core.types.results import (
    PkgcheckResult,
    PkgcheckResultPriority,
    PkgcheckResultsGroup,
)


class StableRequest(BaseModel):
    """
    Stabilization candidate representation.
    """
    model_config = ConfigDict(frozen=True)

    #: Category name.
    category: str = Field(min_length=1)

    #: Package name.
    package: str = Field(min_length=1)

    #: Package version.
    version: str = Field(min_length=1)

    #: Message from pkgcheck.
    message: str = Field(min_length=1)

    @property
    def as_pkgcheck(self) -> PkgcheckResultsGroup:
        """
        Equivalent :py:class:`PkgcheckResultsGroup` object.
        """

        return {
            "atom": "/".join([self.category, self.package]),
            "results": {
                PkgcheckResult(
                    priority=PkgcheckResultPriority(
                        level="info",
                        color="green",
                    ),
                    name="PotentialStable",
                    desc=f"version {self.version}: {self.message}",
                )
            }
        }
