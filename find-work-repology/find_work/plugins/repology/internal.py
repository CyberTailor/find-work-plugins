# SPDX-License-Identifier: WTFPL
# SPDX-FileCopyrightText: 2024 Anna <cyber@sysrq.in>
# No warranty

"""
Internal functions that don't depend on any CLI functionality.
"""

from collections.abc import Collection

import gentoopm
import repology_client
import repology_client.exceptions
from gentoopm.basepm.atom import PMAtom
from pydantic import validate_call
from repology_client.types import Package
from sortedcontainers import SortedSet

from find_work.core.cli.options import MainOptions
from find_work.core.types.results import VersionBump
from find_work.core.utils import aiohttp_session

from find_work.plugins.repology.options import RepologyOptions

PackageSet = set[Package]
ProjectsMapping = dict[str, PackageSet]


@validate_call
async def fetch_outdated(options: MainOptions) -> ProjectsMapping:
    plugin_options = RepologyOptions.model_validate(
        options.children["repology"]
    )

    filters: dict = {}
    if options.maintainer:
        filters["maintainer"] = options.maintainer

    async with aiohttp_session() as session:
        return await repology_client.get_projects(inrepo=plugin_options.repo,
                                                  outdated="on", count=5_000,
                                                  session=session, **filters)


def collect_version_bumps(data: Collection[PackageSet],
                          options: MainOptions) -> SortedSet[VersionBump]:
    plugin_options = RepologyOptions.model_validate(
        options.children["repology"]
    )
    pm = gentoopm.get_package_manager()

    result: SortedSet[VersionBump] = SortedSet()
    for packages in data:
        latest_pkgs: dict[str, PMAtom] = {}  # latest in repo, not across repos!
        new_version: str | None = None

        for pkg in packages:
            if pkg.status == "outdated" and pkg.repo == plugin_options.repo:
                # "pkg.version" can contain spaces, better avoid it!
                origversion = pkg.origversion or pkg.version
                atom = pm.Atom(f"={pkg.visiblename}-{origversion}")

                latest = latest_pkgs.get(pkg.visiblename)
                if latest is None or atom.version > latest.version:
                    latest_pkgs[pkg.visiblename] = atom
            elif pkg.status == "newest":
                new_version = pkg.version

        for latest in latest_pkgs.values():
            if not (options.only_installed and latest.key not in pm.installed):
                result.add(VersionBump(str(latest.key), str(latest.version),
                                       new_version or "(unknown)"))
    return result
