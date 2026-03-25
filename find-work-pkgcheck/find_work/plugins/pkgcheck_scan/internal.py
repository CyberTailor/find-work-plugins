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


def _get_packages_for_maintainer(repo_path: Path, maintainer: str) -> list[str]:
    """
    Find packages matching a maintainer by scanning metadata.xml files.
    """
    packages = []
    for metadata in sorted(repo_path.glob("*/*/metadata.xml")):
        content = metadata.read_text()
        cat = metadata.parent.parent.name
        pkg = metadata.parent.name
        if maintainer == "maintainer-needed@gentoo.org":
            if "<maintainer" not in content:
                packages.append(f"{cat}/{pkg}")
        elif maintainer in content:
            packages.append(f"{cat}/{pkg}")
    return packages


@validate_call
def do_pkgcheck_scan(options: MainOptions) -> SortedDict[
    str, SortedSet[PkgcheckResult]
]:
    plugin_options = PkgcheckOptions.model_validate(
        options.children["pkgcheck"]
    )

    need_repo_obj = bool(options.category or options.maintainer)
    need_pm = bool(need_repo_obj or options.only_installed)

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

    cli_opts: list[str] = [
        "--repo", plugin_options.repo,
        "--scope", "pkg,ver",
        "--filter", "latest",  # TODO: become version-aware
    ]
    if plugin_options.jobs > 0:
        cli_opts += ["--jobs", str(plugin_options.jobs)]
    if plugin_options.keywords:
        cli_opts += ["--keywords", ",".join(plugin_options.keywords)]

    if options.maintainer:
        packages = _get_packages_for_maintainer(
            Path(repo.location), options.maintainer
        )
        if options.category:
            packages = [p for p in packages
                        if p.startswith(options.category + "/")]
        cli_opts.extend(str(Path(repo.location) / pkg) for pkg in packages)
    elif options.category:
        category_path = Path(repo.location) / options.category
        cli_opts.append(str(category_path))

    data: SortedDict[str, SortedSet[PkgcheckResult]] = SortedDict()
    for result in pkgcheck.scan(cli_opts):
        if plugin_options.message:
            if plugin_options.message not in result.desc:
                continue

        package: str = "/".join([result.category, result.package])

        if options.only_installed:
            pkg_atom = atom(package).unversioned_atom
            if pkg_atom not in pm.installed:
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
