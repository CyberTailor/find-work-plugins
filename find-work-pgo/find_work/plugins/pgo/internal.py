# SPDX-License-Identifier: WTFPL
# SPDX-FileCopyrightText: 2024 Anna <cyber@sysrq.in>
# No warranty

"""
Internal functions that don't depend on any CLI functionality.
"""

from collections.abc import Set

import gentoopm
from gentoopm.basepm import PackageManager
from pydantic import TypeAdapter, validate_call
from sortedcontainers import SortedList

from find_work.core.cli.options import MainOptions
from find_work.core.types.results import PkgcheckResultsGroup
from find_work.core.utils import aiohttp_session

from find_work.plugins.pgo.constants import PGO_BASE_URL
from find_work.plugins.pgo.types import StableRequest


@validate_call
async def _fetch_json_stabilization(url: str) -> Set[StableRequest]:
    async with aiohttp_session() as session:
        async with session.get(url, raise_for_status=True) as response:
            raw_data = await response.read()

    return TypeAdapter(Set[StableRequest]).validate_json(raw_data)


@validate_call(validate_return=True)
async def fetch_stabilization(options: MainOptions) -> Set[StableRequest]:
    fetch_all = not bool(options.category or options.maintainer)
    if fetch_all:
        all_url = PGO_BASE_URL + "/packages/stabilization.json"
        return await _fetch_json_stabilization(all_url)

    result: Set[StableRequest] = set()
    if options.category:
        cat_url = (
            PGO_BASE_URL
            + f"/categories/{options.category}/stabilization.json"
        )
        result |= await _fetch_json_stabilization(cat_url)
    if options.maintainer:
        maint_url = (
            PGO_BASE_URL
            + f"/maintainer/{options.maintainer}/stabilization.json"
        )
        result |= await _fetch_json_stabilization(maint_url)
    return result


@validate_call
def collect_stable_requests(
    data: Set[StableRequest],
    options: MainOptions
) -> SortedList[PkgcheckResultsGroup]:

    pm: PackageManager
    if options.only_installed:
        pm = gentoopm.get_package_manager()

    result: SortedList[PkgcheckResultsGroup] = SortedList(
        key=lambda x: x["atom"]
    )
    for item in data:
        if options.only_installed:
            atom = "/".join([item.category, item.package])
            if atom not in pm.installed:
                continue
        result.add(item.as_pkgcheck)
    return result
