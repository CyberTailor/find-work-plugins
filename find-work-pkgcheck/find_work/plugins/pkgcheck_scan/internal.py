# SPDX-License-Identifier: WTFPL
# SPDX-FileCopyrightText: 2024-2026 Anna <cyber@sysrq.in>
# No warranty

"""
Internal functions that don't depend on any CLI functionality.
"""

import os
from functools import cache
from pathlib import Path

import pkgcheck
import pkgcore.config
import pkgcore.ebuild.repository
import pkgcore.vdb.ondisk
from pkgcore.ebuild.atom import atom
from pkgcore.ebuild.repo_objs import LocalMetadataXml, RepoConfig
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


@cache
def _get_repo_location(path_or_name: str) -> Path:
    pm = PkgcorePM()
    repo = (
        pm.repo_from_path(repo_path)
        if (repo_path := Path(path_or_name).resolve()).is_dir()
        else pm.repo_from_name(path_or_name)
    )

    return Path(repo.location)


def get_packages_for_maintainer(options: MainOptions) -> list[str]:
    """
    Find packages matching a maintainer by scanning metadata.xml files.

    :returns: list of paths to filtered packages
    """

    plugin_options = PkgcheckOptions.model_validate(
        options.children["pkgcheck"]
    )

    repo_path = _get_repo_location(plugin_options.repo)
    category = options.category or "*"
    packages = []
    for metadata in sorted(repo_path.glob(category + "/*/metadata.xml")):
        cat = metadata.parent.parent.name
        pkg = metadata.parent.name
        emails: set[str | None] = {
            maint.email.strip()
            for maint in LocalMetadataXml(metadata).maintainers
        }
        if options.maintainer not in emails:
            if options.maintainer == "maintainer-needed@gentoo.org":
                if len(emails) != 0:
                    continue
            else:
                continue
        packages.append(str(repo_path / cat / pkg))
    return packages


@validate_call
def do_pkgcheck_scan(
    options: MainOptions, packages: list[str] | None = None
) -> SortedDict[str, SortedSet[PkgcheckResult]]:

    plugin_options = PkgcheckOptions.model_validate(
        options.children["pkgcheck"]
    )

    pm: PkgcorePM
    if options.only_installed:
        pm = PkgcorePM()

    cli_opts: list[str] = [
        "--repo", plugin_options.repo,
        "--scope", "pkg,ver",
        "--filter", "latest",  # TODO: become version-aware
    ]
    if plugin_options.jobs > 0:
        cli_opts += ["--jobs", str(plugin_options.jobs)]
    if plugin_options.keywords:
        cli_opts += ["--keywords", ",".join(plugin_options.keywords)]

    # Scan targets
    if packages:
        cli_opts.extend(packages)
    elif options.category:
        category_path = _get_repo_location(plugin_options.repo) / options.category
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
