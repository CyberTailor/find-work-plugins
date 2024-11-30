# SPDX-License-Identifier: WTFPL
# SPDX-FileCopyrightText: 2024 Anna <cyber@sysrq.in>
# No warranty

"""
Internal functions that don't depend on any CLI functionality.
"""

import os
from pathlib import Path

import pkgcheck
import pkgcore.config
import pkgcore.ebuild.repository
import pkgcore.vdb.ondisk
from pkgcore.ebuild.atom import atom
from pkgcore.ebuild.repo_objs import RepoConfig
from pkgcore.ebuild.repository import UnconfiguredTree
from pydantic import validate_call
from sortedcontainers import SortedDict, SortedSet

from find_work.core.cli.options import MainOptions
from find_work.core.types.results import (
    PkgcheckResult,
    PkgcheckResultPriority,
)

from find_work.plugins.pkgcheck_scan.options import PkgcheckOptions


class PkgcorePM:

    def __init__(self) -> None:
        config_root = os.environ.get("PORTAGE_CONFIGROOT", "")
        kwargs = {}
        if config_root != "":
            kwargs["location"] = str(Path(config_root) / "etc" / "portage")

        self._config = pkgcore.config.load_config(**kwargs)
        self._domain = self._config.get_default("domain")

    @property
    def installed(self) -> pkgcore.vdb.ondisk.tree:
        return self._domain.repos_raw["vdb"]

    @validate_call
    def repo_from_name(self, name: str) -> UnconfiguredTree:
        return self._domain.ebuild_repos_raw[name]

    @validate_call
    def repo_from_path(self, path: str | Path) -> UnconfiguredTree:
        repo_config = RepoConfig(location=str(path))
        return pkgcore.ebuild.repository.tree(self._config, repo_config)


@validate_call
def do_pkgcheck_scan(options: MainOptions) -> SortedDict[
    str, SortedSet[PkgcheckResult]
]:
    plugin_options = PkgcheckOptions.model_validate(
        options.children["pkgcheck"]
    )

    need_repo_obj = bool(options.maintainer)
    need_pm = need_repo_obj or options.only_installed

    pm: PkgcorePM
    repo: UnconfiguredTree
    if need_pm:
        pm = PkgcorePM()
        if need_repo_obj:
            repo = (
                pm.repo_from_path(repo_path)
                if (repo_path := Path(plugin_options.repo).resolve()).is_dir()
                else pm.repo_from_name(plugin_options.repo)
            )

    cli_opts = [
        "--repo", plugin_options.repo,
        "--scope", "pkg,ver",
        "--filter", "latest",  # TODO: become version-aware
    ]
    if plugin_options.keywords:
        cli_opts += ["--keywords", ",".join(plugin_options.keywords)]

    data: SortedDict[str, SortedSet[PkgcheckResult]] = SortedDict()
    for result in pkgcheck.scan(cli_opts):
        if plugin_options.message:
            if plugin_options.message not in result.desc:
                continue

        package = "/".join([result.category, result.package])
        pkg_atom: atom
        if need_pm:
            pkg_atom = atom(package).unversioned_atom

        if options.only_installed:
            if pkg_atom not in pm.installed:
                continue

        if options.maintainer == "maintainer-needed@gentoo.org":
            for pkg_match in repo.itermatch(pkg_atom):
                if len(pkg_match.maintainers) == 0:
                    break
            else:
                continue
        elif options.maintainer:
            maint_matched = False
            for pkg_match in repo.itermatch(pkg_atom):
                for maint in pkg_match.maintainers:
                    if maint.email == options.maintainer:
                        maint_matched = True
                        break

                if maint_matched:
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
