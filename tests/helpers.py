"""Shared test fixtures for cross-module scenario tests."""

from __future__ import annotations

from pathlib import Path

from artifact_store import ArtifactStore


def seed_store(store: ArtifactStore, *, with_task: bool = True) -> None:
    """Seed a representative authoritative artifact graph."""
    store.init()
    store.write(
        "product/auth",
        "product-spec",
        "## acceptance\nA user can log in with email.\n## scope\nemail login",
        status="accepted",
    )
    store.write(
        "technical/auth",
        "technical-spec",
        "## contract.login\nPOST /auth/login -> {token}.",
        status="accepted",
    )
    store.write(
        "decisions/auth-provider",
        "decisions",
        "## constraint\nUse local provider only.\n",
        status="accepted",
    )
    store.write(
        "roadmap/auth",
        "roadmap",
        "## acceptance\nP5 verification loop ships.\n## milestone\nP5 ships a verification loop.\n",
        status="accepted",
    )
    store.write(
        "project-state",
        "project-state",
        "## stage\nEXECUTION\n## task\ntasks/auth-01\n## blocker\nnone\n",
        status="accepted",
    )
    if with_task:
        store.write(
            "tasks/auth-01",
            "tasks",
            "## id\ntasks/auth-01\n## title\nimpl auth\n## acceptance\nlogin works\n"
            "## status\nproposed\n## priority\n1\n## depends_on\n\n",
            status="accepted",
        )


def seeded_store(root: Path) -> ArtifactStore:
    store = ArtifactStore(root)
    seed_store(store)
    return store
