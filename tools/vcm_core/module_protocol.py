"""Shared machine-readable result envelope for VCM internal modules."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


VALID_STATUSES = frozenset({"complete", "ready", "blocked", "failed"})


@dataclass
class ModuleResult:
    """Stable handoff envelope used by the workflow router."""

    module_id: str
    status: str
    artifacts: list[Any] = field(default_factory=list)
    evidence: list[Any] = field(default_factory=list)
    blockers: list[Any] = field(default_factory=list)
    next_action: str = ""
    contract_version: str = "v1"

    def __post_init__(self) -> None:
        if self.status not in VALID_STATUSES:
            raise ValueError(f"invalid module status: {self.status}")

    def as_dict(self) -> dict[str, Any]:
        return {
            "module_id": self.module_id,
            "contract_version": self.contract_version,
            "status": self.status,
            "artifacts": list(self.artifacts),
            "evidence": list(self.evidence),
            "blockers": list(self.blockers),
            "next_action": self.next_action,
        }


def complete(module_id: str, *, artifacts: list[Any] | None = None,
             evidence: list[Any] | None = None, next_action: str = "") -> dict[str, Any]:
    return ModuleResult(module_id, "complete", artifacts or [], evidence or [], [], next_action).as_dict()


def ready(module_id: str, *, artifacts: list[Any] | None = None,
          evidence: list[Any] | None = None, next_action: str = "") -> dict[str, Any]:
    """Return a valid handoff when a module is ready for the next gate."""
    return ModuleResult(module_id, "ready", artifacts or [], evidence or [], [], next_action).as_dict()


def blocked(module_id: str, blockers: list[Any], *, next_action: str = "") -> dict[str, Any]:
    return ModuleResult(module_id, "blocked", blockers=blockers, next_action=next_action).as_dict()


def failed(module_id: str, blockers: list[Any], *, next_action: str = "") -> dict[str, Any]:
    return ModuleResult(module_id, "failed", blockers=blockers, next_action=next_action).as_dict()
