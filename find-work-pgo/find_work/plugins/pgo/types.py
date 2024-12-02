# SPDX-License-Identifier: WTFPL
# SPDX-FileCopyrightText: 2024-2025 Anna <cyber@sysrq.in>
# No warranty

"""
Internal type definitions for Gentoo Packages API, implemented as Pydantic
models.
"""

from pydantic import BaseModel, ConfigDict, Field

from find_work.core.types.results import (
    PkgcheckResult,
    PkgcheckResultPriority,
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
    def as_pkgcheck(self) -> PkgcheckResult:
        """
        Corresponding pkgcheck result.

        >>> request = StableRequest.model_validate_json('''
        ...     {
        ...         "category": "dev-foo",
        ...         "package": "nya",
        ...         "version": "1.0",
        ...         "message": "slot(0) no change in 90 days for unstable keyword: [ ~amd64 ]"
        ...     }
        ... ''')
        >>> request.as_pkgcheck  # doctest: +NORMALIZE_WHITESPACE
        PkgcheckResult(priority=PkgcheckResultPriority(level='info',
                                                       color='green'),
                       name='PotentialStable',
                       desc='version 1.0: slot(0) no change in 90 days for
                             unstable keyword: [ ~amd64 ]')
        """

        return PkgcheckResult(
            priority=PkgcheckResultPriority(
                level="info",
                color="green",
            ),
            name="PotentialStable",
            desc=f"version {self.version}: {self.message}",
        )
