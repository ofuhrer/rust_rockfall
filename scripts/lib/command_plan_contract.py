from __future__ import annotations

"""Shared command-plan manifest helpers.

The helpers keep command-plan records explicit while avoiding duplicated
manifest semantics across generators. They only shape metadata; they do not
execute or rewrite the commands they describe.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence
import shlex


@dataclass(frozen=True)
class CommandPlanEntry:
    """A command-plan manifest entry with read/write and output-root semantics."""

    command_id: str
    group: str
    description: str
    command: str
    expected_inputs: Sequence[str]
    expected_outputs: Sequence[str]
    read_only: bool
    may_produce_ignored_outputs: bool
    site: str | None = None
    blocked_reason: str = ""
    ignored_output_paths: Sequence[str] = field(default_factory=tuple)
    output_profile_policy: Mapping[str, Any] | None = None
    extra_fields: Mapping[str, Any] = field(default_factory=dict)
    include_none_extra_fields: Sequence[str] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        record: dict[str, Any] = {}
        if self.site is not None:
            record["site"] = self.site
        record.update(
            {
                "group": self.group,
                "id": self.command_id,
                "description": self.description,
                "command": self.command,
                "expected_inputs": list(self.expected_inputs),
                "expected_outputs": list(self.expected_outputs),
            }
        )
        for key, value in self.extra_fields.items():
            if value is not None or key in self.include_none_extra_fields:
                record[key] = value
        record.update(
            {
                "blocked_reason": self.blocked_reason,
                "read_only": bool(self.read_only),
                "may_produce_ignored_outputs": bool(self.may_produce_ignored_outputs),
                "ignored_output_paths": list(self.ignored_output_paths),
            }
        )
        if self.output_profile_policy is not None:
            record["output_profile_policy"] = dict(self.output_profile_policy)
        return record


def build_command_record(
    *,
    command_id: str,
    group: str,
    description: str,
    command: str,
    expected_inputs: Sequence[str],
    expected_outputs: Sequence[str],
    read_only: bool,
    may_produce_ignored_outputs: bool,
    site: str | None = None,
    blocked_reason: str = "",
    ignored_output_paths: Sequence[str] | None = None,
    output_profile_policy: Mapping[str, Any] | None = None,
    extra_fields: Mapping[str, Any] | None = None,
    include_none_extra_fields: Sequence[str] = (),
) -> dict[str, Any]:
    return CommandPlanEntry(
        command_id=command_id,
        group=group,
        description=description,
        command=command,
        expected_inputs=expected_inputs,
        expected_outputs=expected_outputs,
        read_only=read_only,
        may_produce_ignored_outputs=may_produce_ignored_outputs,
        site=site,
        blocked_reason=blocked_reason,
        ignored_output_paths=ignored_output_paths or (),
        output_profile_policy=output_profile_policy,
        extra_fields=extra_fields or {},
        include_none_extra_fields=include_none_extra_fields,
    ).to_dict()


def summarize_command_groups(
    commands: Sequence[Mapping[str, Any]],
    *,
    group_order: Sequence[str],
    group_descriptions: Mapping[str, str],
    ignored_output_paths: Sequence[str],
    site: str | None = None,
    include_site: bool = True,
    include_manifest_semantics: bool = True,
) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for group_id in group_order:
        group_commands = [command for command in commands if command["group"] == group_id]
        if not group_commands:
            continue
        summary: dict[str, Any] = {
            "id": group_id,
            "description": group_descriptions[group_id],
            "command_ids": [str(command["id"]) for command in group_commands],
            "status": "blocked_template" if any(command.get("blocked_reason") for command in group_commands) else "ready",
        }
        if include_site and site is not None:
            summary = {"site": site, **summary}
        if include_manifest_semantics:
            summary.update(
                {
                    "read_only": all(bool(command["read_only"]) for command in group_commands),
                    "may_produce_ignored_outputs": any(
                        bool(command["may_produce_ignored_outputs"]) for command in group_commands
                    ),
                    "ignored_output_paths": list(ignored_output_paths),
                }
            )
        summaries.append(summary)
    return summaries


def command_ids(commands: Sequence[Mapping[str, Any]]) -> list[str]:
    return [str(command["id"]) for command in commands]


def command_descriptions(commands: Sequence[Mapping[str, Any]]) -> dict[str, str]:
    return {str(command["id"]): str(command["description"]) for command in commands}


def blocked_command_ids(commands: Sequence[Mapping[str, Any]]) -> list[str]:
    return sorted(str(command["id"]) for command in commands if command.get("blocked_reason"))


def command_string(parts: Sequence[str]) -> str:
    return shlex.join(list(parts))


def relative_path(path: Path, *, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)
