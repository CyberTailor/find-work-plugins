# SPDX-License-Identifier: WTFPL
# SPDX-FileCopyrightText: 2024 Anna <cyber@sysrq.in>
# No warranty

"""
Internal functions that don't depend on any CLI functionality.
"""

import logging
import warnings
from collections.abc import Collection
from datetime import datetime
from typing import Any

import gentoopm
import pydantic_core
from pydantic import validate_call

from find_work.core.cli.options import MainOptions
from find_work.core.types.results import BugView
from find_work.core.utils import (
    extract_package_name,
    requests_session,
)

from find_work.plugins.gentoo_bugzilla.constants import BUGZILLA_URL
from find_work.plugins.gentoo_bugzilla.options import BugzillaOptions

with warnings.catch_warnings():
    # Disable annoying warning shown to LibreSSL users
    warnings.simplefilter("ignore")
    import bugzilla
    from bugzilla.bug import Bug

logger = logging.getLogger("find_work.plugins.bugzilla")


@validate_call
def bugs_from_raw_json(raw_json: str | bytes) -> list[Bug]:
    data: list[dict] = pydantic_core.from_json(raw_json)
    with requests_session() as session:
        bz = bugzilla.Bugzilla(BUGZILLA_URL, requests_session=session,
                               force_rest=True)
        return [Bug(bz, dict=bug) for bug in data]


def bugs_to_raw_json(data: Collection[Bug]) -> bytes:
    raw_data = [bug.get_raw_data() for bug in data]
    return pydantic_core.to_json(raw_data, exclude_none=True)


@validate_call
def fetch_bugs(options: MainOptions, **kwargs: Any) -> list[Bug]:
    plugin_options = BugzillaOptions.model_validate(
        options.children["bugzilla"]
    )

    with requests_session() as session:
        bz = bugzilla.Bugzilla(BUGZILLA_URL, requests_session=session,
                               force_rest=True)
        query = bz.build_query(
            short_desc=plugin_options.short_desc or None,
            product=plugin_options.product or None,
            component=plugin_options.component or None,
            assigned_to=options.maintainer or None,
        )
        query["resolution"] = "---"
        if plugin_options.chronological_sort:
            query["order"] = "changeddate DESC"
        else:
            query["order"] = "bug_id DESC"
        return bz.query(query)


def collect_bugs(data: Collection[Bug], options: MainOptions) -> list[BugView]:
    if options.only_installed:
        pm = gentoopm.get_package_manager()

    result: list[BugView] = []
    for bug in data:
        if options.only_installed:
            if (package := extract_package_name(bug.summary)) is None:
                continue

            is_installed = False
            try:
                is_installed = package in pm.installed
            except gentoopm.exceptions.InvalidAtomStringError:
                logger.warning("Invalid atom parsed: '%s', please report a bug",
                               package)

            if not is_installed:
                continue

        date = datetime.fromisoformat(bug.last_change_time).date().isoformat()
        item = BugView(bug.id, date, bug.assigned_to, bug.summary)
        result.append(item)
    return result
