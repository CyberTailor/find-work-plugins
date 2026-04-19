# SPDX-License-Identifier: WTFPL
# SPDX-FileCopyrightText: 2025-2026 Anna <cyber@sysrq.in>
# No warranty

"""
Results reporter for Repology results, such as repository problems.
"""

from repology_client.types import CPE, Problem
from repology_client.utils import format_link_status

from find_work.core.reporters import AbstractReporter

from find_work.plugins.repology.types import ProblemGroup


def format_problem_type(problem: Problem) -> str:
    """
    :returns: problem type, converted from snake_case to PascalCase
    """
    return "".join(word.title() for word in problem.type.split("_"))


def format_problem_info(problem: Problem) -> str:
    """
    Source: https://github.com/repology/repology-rs/blob/master/repology-webapp/templates/problems/index.html
    """  # noqa
    result: str
    match problem.type:
        case "homepage_dead":
            url = problem.data.get("url", "url is missing")
            code = problem.data.get("code")
            status = (
                format_link_status(code)
                if isinstance(code, int)
                else "code is bad or missing"
            )
            result = (
                "Homepage link <{url}> is dead ({status}) for more than a "
                "month and should be replaced by alive link (see other "
                "packages for hints, or link to archive.org as a last resort)."
            ).format(url=url, status=status)
        case "homepage_permanent_https_redirect":
            url = problem.data.get("url", "url is missing")
            target = problem.data.get("target", "target is missing")
            result = (
                "Homepage link <{url}> is a permanent redirect to its HTTPS "
                "counterpart <{target}> and should be updated."
            ).format(url=url, target=target)
        case "homepage_discontinued_google":
            url = problem.data.get("url", "url is missing")
            result = (
                "Homepage link <{url}> points to Google Code which was "
                "discontinued. The link should be updated (probably along with "
                "download URLs). If this link is still alive, it may point to "
                "a new project homepage."
            ).format(url=url)
        case "homepage_discontinued_codeplex":
            url = problem.data.get("url", "url is missing")
            result = (
                "Homepage link <{url}> points to codeplex which was "
                "discontinued. The link should be updated (probably along "
                "with download URLs)."
            ).format(url=url)
        case "homepage_discontinued_gna":
            url = problem.data.get("url", "url is missing")
            result = (
                "Homepage link <{url}> points to Gna which was discontinued. "
                "The link should be updated (probably along with download "
                "URLs)."
            ).format(url=url)
        case "homepage_discontinued_cpan":
            url = problem.data.get("url", "url is missing")
            result = (
                "Homepage link <{url}> points to CPAN which was discontinued. "
                "The link should be updated to MetaCPAN (probably along with "
                "download URLs)."
            ).format(url=url)
        case "cpe_unreferenced":
            cpe_struct = problem.data.get("cpe")
            cpe = (
                str(CPE.model_validate(cpe_struct))
                if isinstance(cpe_struct, dict)
                else "CPE is bad or missing."
            )
            result = (
                "CPE information defined for the package: {cpe} was not found "
                "neither among known CVEs nor in NVD CPE dictionary, so it "
                "may be invalid."
            ).format(cpe=cpe)
            if isinstance(suggestions := problem.data.get("suggestions"), list):
                suggested_cpes = [
                    str(CPE.model_validate(cpe_struct))
                    for cpe_struct in suggestions
                    if isinstance(cpe_struct, dict)
                ]
                result += (
                    " Suggested CPEs (as per known {project_name} CVEs): "
                    "{suggestions}."
                ).format(project_name=problem.project_name,
                         suggestions=", ".join(suggested_cpes))
        case "cpe_missing":
            result = (
                "CPE information is missing for this package, while repository "
                "defines it for other packages."
            )
            if isinstance(suggestions := problem.data.get("suggestions"), list):
                suggested_cpes = [
                    str(CPE.model_validate(cpe_struct))
                    for cpe_struct in suggestions
                    if isinstance(cpe_struct, dict)
                ]
                result += (
                    " Suggested CPEs (as per known {project_name} CVEs): "
                    "{suggestions}."
                ).format(project_name=problem.project_name,
                         suggestions=", ".join(suggested_cpes))
        case "download_dead":
            url = problem.data.get("url", "url is missing")
            code = problem.data.get("code")
            status = (
                format_link_status(code)
                if isinstance(code, int)
                else "code is bad or missing"
            )
            result = (
                "Download link <{url}> is dead ({status}) for more than a "
                "month and should be replaced by alive link (see other "
                "packages for hints)."
            ).format(url=url, status=status)
        case "download_permanent_https_redirect":
            url = problem.data.get("url", "url is missing")
            target = problem.data.get("target", "target is missing")
            result = (
                "Download link <{url}> is a permanent redirect to its HTTPS "
                "counterpart <{target}> and should be updated."
            ).format(url=url, target=target)
        case "homepage_sourceforge_missing_trailing_slash":
            url = problem.data.get("url", "url is missing")
            result = (
                "Homepage link <{url}> needs a trailing slash added, otherwise "
                "there's a javascript redirect."
            ).format(url=url)
        case _:
            result = (
                "Unformatted problem of type {problem.type}, "
                "data={problem.data}. The template should be updated, please "
                "report this."
            ).format(problem=problem)

    return result


class ConsoleProblemReporter(AbstractReporter[ProblemGroup]):
    reporter_name = "console"
    result_type = ProblemGroup

    def add_result(self, item: ProblemGroup) -> None:
        self.options.echo()
        self.options.secho(item["atom"], fg="cyan", bold=True)

        for problem in item["problems"]:
            self.options.echo("\t", nl=False)
            self.options.secho(format_problem_type(problem),
                               fg="yellow", nl=False)
            self.options.echo(": ", nl=False)
            self.options.echo(format_problem_info(problem))
