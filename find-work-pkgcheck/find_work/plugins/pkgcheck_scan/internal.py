# SPDX-License-Identifier: WTFPL
# SPDX-FileCopyrightText: 2024 Anna <cyber@sysrq.in>
# No warranty

"""
Internal functions that don't depend on any CLI functionality.
"""

import gentoopm
import pkgcheck
from gentoopm.basepm.repo import PMRepository
from pydantic import validate_call
from sortedcontainers import SortedDict, SortedSet

from find_work.core.cli.options import MainOptions
from find_work.core.types.results import (
    PkgcheckResult,
    PkgcheckResultPriority,
)

from find_work.plugins.pkgcheck_scan.options import PkgcheckOptions


@validate_call
def do_pkgcheck_scan(options: MainOptions) -> SortedDict[
    str, SortedSet[PkgcheckResult]
]:
    plugin_options = PkgcheckOptions.model_validate(
        options.children["pkgcheck"]
    )

    repo_obj: PMRepository
    if options.only_installed or options.maintainer:
        pm = gentoopm.get_package_manager()
        if options.maintainer:
            repo_obj = pm.repositories[plugin_options.repo]

    cli_opts = [
        "--repo", plugin_options.repo,
        "--scope", "pkg,ver",
        "--filter", "latest",  # TODO: become version-aware
    ]
    if plugin_options.keywords:
        cli_opts += ["--keywords", ",".join(plugin_options.keywords)]

    data: SortedDict[str, SortedSet[PkgcheckResult]] = SortedDict()
    for result in pkgcheck.scan(cli_opts):
        if plugin_options.message not in result.desc:
            continue

        package = "/".join([result.category, result.package])
        if options.only_installed and package not in pm.installed:
            continue
        if options.maintainer:
            for maint in repo_obj.select(package).maintainers:
                if maint.email == options.maintainer:
                    break
            else:
                continue
        data.setdefault(package, SortedSet()).add(
            PkgcheckResult(
                priority=PkgcheckResultPriority(
                    level=result.level or "N/A",
                    color=result.color or "",
                ),
                name=result.name or "N/A",
                desc=result.desc or "N/A",
            )
        )
    return data
