# SPDX-License-Identifier: WTFPL
# SPDX-FileCopyrightText: 2026 Anna <cyber@sysrq.in>
# No warranty

"""
Internal type definitions.
"""

from collections.abc import Sequence
from typing import TypedDict

from repology_client.types import Problem


class ProblemGroup(TypedDict):
    """
    A group of problems belonging to the same package.
    """

    #: Package name.
    atom: str

    #: Problems.
    problems: Sequence[Problem]
