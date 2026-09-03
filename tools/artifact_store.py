#!/usr/bin/env python3
"""Typed authority-artifact store (P2 runtime, deterministic, stdlib only).

Implements the local half of docs/artifact-context-contract.md: artifacts are keyed by
artifact_id with a sha256 content hash and a sidecar JSON metadata file. No provider,
no external dependency; each write is content-addressed and revisioned so the store is
idempotent and rollback-safe.

Usage:
  python tools/artifact_store.py init --root <project>
  python tools/artifact_store.py write --root <project> product/auth --kind product-spec --file spec.md
  python tools/artifact_store.py write --root <project> decisions/auth --kind decisions --status accepted --text "use provider X"
  python tools/artifact_store.py list --root <project>
  python tools/artifact_store.py get --root <project> product/auth
  python tools/artifact_store.py validate --root <project>
  python tools/artifact_store.py hash < file.txt
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# Authority artifact kinds exactly as documented in docs/artifact-context-contract.md.
KINDS = (
    "analysis",
    "product-spec",
    "design-brief",
    "technical-spec",
    "decisions",
    "roadmap",
    "tasks",
    "project-state",
    "receipts",
    "experience",
    "archive",
)
# Accepted lifecycle statuses; an inference stays draft until its gate accepts it.
STATUSES = ("draft", "review", "accepted", "superseded", "archived")

ARTIFACTS_DIR = "artifacts"
META_DIR = ".meta"
ID_RE = r"^[a-z0-9][a-z0-9/_.-]*$"
# The artifact_id's first path segment is a namespace shorthand that maps to the
# authority-artifact kind (contract examples: product/auth -> product-spec).
ID_PREFIXES = {
    "analysis": "analysis",
    "product": "product-spec",
    "design": "design-brief",
    "technical": "technical-spec",
    "decisions": "decisions",
    "roadmap": "roadmap",
    "tasks": "tasks",
    "project-state": "project-state",
    "receipts": "receipts",
    "experience": "experience",
    "archive": "archive",
}


@dataclasses.dataclass
class ArtifactMetadata:
    """Machine-readable metadata for one authority artifact (contract section 2)."""

    artifact_id: str
    kind: str
    revision: int
    status: str
    content_hash: str
    updated_at: str
    depends_on: list[str] = dataclasses.field(default_factory=list)
    supersedes: str | None = None
    l0_ref: str | None = None
    l1_ref: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "ArtifactMetadata":
        return cls(
            artifact_id=data["artifact_id"],
            kind=data["kind"],
            revision=int(data["revision"]),
            status=data["status"],
            content_hash=data["content_hash"],
            updated_at=data["updated_at"],
            depends_on=list(data.get("depends_on", [])),
            supersedes=data.get("supersedes"),
            l0_ref=data.get("l0_ref"),
            l1_ref=data.get("l1_ref"),
        )

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclasses.dataclass
class Artifact:
    """An artifact: its metadata plus the current content bytes."""

    metadata: ArtifactMetadata
    content: str


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def content_hash(content: str) -> str:
    """Return a deterministic 'sha256:<hex>' reference for artifact content."""
    return "sha256:" + sha256_hex(content.encode("utf-8"))


def split_ref(ref: str) -> tuple[str, int | None]:
    """Split 'product/auth@7' -> ('product/auth', 7). A missing revision is None."""
    if "@" in ref:
        artifact_id, rev = ref.rsplit("@", 1)
        return artifact_id, int(rev)
    return ref, None


class ArtifactStore:
    """Persist authority artifacts under <root>/artifacts with sidecar JSON metadata."""

    def __init__(self, root: Path):
        self.root = Path(root)
        self.dir = self.root / ARTIFACTS_DIR
        self.meta_dir = self.dir / META_DIR

    # ----- helpers -----
    def _content_path(self, artifact_id: str) -> Path:
        return self.dir / (artifact_id + ".md")

    def _meta_path(self, artifact_id: str) -> Path:
        return self.meta_dir / (artifact_id + ".json")

    @staticmethod
    def _validate_id(artifact_id: str) -> None:
        import re

        if not artifact_id or not re.fullmatch(ID_RE, artifact_id):
            raise ValueError(f"invalid artifact_id: {artifact_id!r}")
        if artifact_id.startswith("."):
            raise ValueError(f"artifact_id must not start with '.': {artifact_id!r}")
        first = artifact_id.split("/", 1)[0]
        if first not in ID_PREFIXES:
            raise ValueError(
                f"artifact_id's first path segment must be a namespace prefix "
                f"({artifact_id!r}); got {first!r}"
            )

    @classmethod
    def _validate_kind_for_id(cls, artifact_id: str, kind: str) -> None:
        cls._validate_kind(kind)
        prefix = artifact_id.split("/", 1)[0]
        expected = ID_PREFIXES[prefix]
        if kind != expected:
            raise ValueError(
                f"artifact_id {artifact_id!r} implies kind {expected!r}, got {kind!r}"
            )

    @staticmethod
    def _validate_kind(kind: str) -> None:
        if kind not in KINDS:
            raise ValueError(f"invalid kind {kind!r}; expected one of {KINDS}")

    @staticmethod
    def _validate_status(status: str) -> None:
        if status not in STATUSES:
            raise ValueError(
                f"invalid status {status!r}; expected one of {STATUSES}"
            )

    @staticmethod
    def split_ref(ref: str) -> tuple[str, int | None]:
        return split_ref(ref)

    # ----- lifecycle -----
    def init(self) -> Path:
        self.dir.mkdir(parents=True, exist_ok=True)
        self.meta_dir.mkdir(parents=True, exist_ok=True)
        return self.dir

    def exists(self, artifact_id: str) -> bool:
        return self._content_path(artifact_id).is_file()

    def get(self, artifact_id: str) -> Artifact:
        self._validate_id(artifact_id)
        content_path = self._content_path(artifact_id)
        meta_path = self._meta_path(artifact_id)
        if not content_path.is_file() or not meta_path.is_file():
            raise KeyError(f"artifact not found: {artifact_id}")
        metadata = ArtifactMetadata.from_dict(
            json.loads(meta_path.read_text(encoding="utf-8"))
        )
        return Artifact(metadata=metadata, content=content_path.read_text(encoding="utf-8"))

    def list(self) -> list[ArtifactMetadata]:
        out: list[ArtifactMetadata] = []
        if not self.meta_dir.is_dir():
            return out
        for meta_file in sorted(self.meta_dir.rglob("*.json")):
            out.append(
                ArtifactMetadata.from_dict(
                    json.loads(meta_file.read_text(encoding="utf-8"))
                )
            )
        return out

    def write(
        self,
        artifact_id: str,
        kind: str,
        content: str,
        *,
        status: str = "draft",
        depends_on: list[str] | None = None,
        supersedes: str | None = None,
        updated_at: str | None = None,
    ) -> ArtifactMetadata:
        """Create or revision an artifact idempotently. Same content+status is a no-op."""
        self._validate_id(artifact_id)
        self._validate_kind_for_id(artifact_id, kind)
        self._validate_status(status)
        if not content.strip():
            raise ValueError("artifact content must not be empty")

        now = updated_at or self._today()
        new_hash = content_hash(content)
        revision = 1

        if self.exists(artifact_id):
            previous = self.get(artifact_id).metadata
            # Idempotent: identical content + status -> return existing metadata.
            if previous.content_hash == new_hash and previous.status == status:
                return previous
            revision = previous.revision + 1
            if supersedes is None:
                supersedes = f"{artifact_id}@{previous.revision}"

        metadata = ArtifactMetadata(
            artifact_id=artifact_id,
            kind=kind,
            revision=revision,
            status=status,
            content_hash=new_hash,
            updated_at=now,
            depends_on=sorted(depends_on or []),
            supersedes=supersedes,
            l0_ref=f"summaries/{artifact_id}.l0",
            l1_ref=f"summaries/{artifact_id}.l1",
        )

        content_path = self._content_path(artifact_id)
        content_path.parent.mkdir(parents=True, exist_ok=True)
        self._atomic_write(content_path, content)

        meta_path = self._meta_path(artifact_id)
        meta_path.parent.mkdir(parents=True, exist_ok=True)
        self._atomic_write(
            meta_path,
            json.dumps(metadata.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        )
        return metadata

    def validate(self) -> list[str]:
        """Return a list of consistency errors (empty means the store is healthy)."""
        errors: list[str] = []
        if not self.dir.is_dir():
            return errors

        ids = set()
        for meta_file in self.meta_dir.rglob("*.json"):
            try:
                data = json.loads(meta_file.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                errors.append(f"unreadable metadata: {meta_file}: {exc}")
                continue
            try:
                metadata = ArtifactMetadata.from_dict(data)
            except (KeyError, ValueError, TypeError) as exc:
                errors.append(f"malformed metadata: {meta_file}: {exc}")
                continue
            ids.add(metadata.artifact_id)
            if metadata.kind not in KINDS:
                errors.append(f"{metadata.artifact_id}: invalid kind {metadata.kind!r}")
            try:
                ArtifactStore._validate_kind_for_id(metadata.artifact_id, metadata.kind)
            except ValueError as exc:
                errors.append(f"{metadata.artifact_id}: {exc}")
            if metadata.status not in STATUSES:
                errors.append(
                    f"{metadata.artifact_id}: invalid status {metadata.status!r}"
                )
            if metadata.revision < 1:
                errors.append(f"{metadata.artifact_id}: revision must be >= 1")
            content_path = self._content_path(metadata.artifact_id)
            if not content_path.is_file():
                errors.append(
                    f"{metadata.artifact_id}: missing content file {content_path.relative_to(self.root)}"
                )
                continue
            actual = content_hash(content_path.read_text(encoding="utf-8"))
            if actual != metadata.content_hash:
                errors.append(
                    f"{metadata.artifact_id}: content hash mismatch "
                    f"(recorded {metadata.content_hash}, actual {actual})"
                )

        # Reference integrity against the index (not the content).
        for metadata in (self.list() if self.meta_dir.is_dir() else []):
            for dep in metadata.depends_on:
                dep_id, _ = self.split_ref(dep)
                if dep_id not in ids:
                    errors.append(f"{metadata.artifact_id}: missing depends_on {dep}")
            if metadata.supersedes:
                sup_id, _ = self.split_ref(metadata.supersedes)
                if sup_id not in ids:
                    errors.append(
                        f"{metadata.artifact_id}: missing supersedes {metadata.supersedes}"
                    )
        return errors

    @staticmethod
    def _today() -> str:
        from datetime import date

        return date.today().isoformat()

    @staticmethod
    def _atomic_write(path: Path, text: str) -> None:
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(text, encoding="utf-8")
        tmp.replace(path)


def _read_text(path: Path) -> str:
    if not path.is_file():
        raise SystemExit(f"not a file: {path}")
    return path.read_text(encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Typed authority-artifact store")
    parser.add_argument("--root", type=Path, required=True, help="project root")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init", help="create the artifacts directory")

    p = sub.add_parser("write", help="create or revision an artifact")
    p.add_argument("artifact_id", help="e.g. product/auth")
    p.add_argument("--kind", required=True, choices=KINDS)
    p.add_argument("--file", type=Path, help="read content from this file")
    p.add_argument("--text", help="content as an inline string")
    p.add_argument("--status", choices=STATUSES, default="draft")
    p.add_argument("--depends-on", action="append", default=[])
    p.add_argument("--supersedes")
    p.add_argument("--updated-at")

    sub.add_parser("list", help="list all artifact metadata")

    p = sub.add_parser("get", help="print an artifact (metadata + content)")
    p.add_argument("artifact_id")

    p = sub.add_parser("validate", help="check store consistency")

    sub.add_parser("hash", help="print the sha256 of stdin")

    args = parser.parse_args()
    store = ArtifactStore(args.root)

    if args.cmd == "init":
        print(store.init())
    elif args.cmd == "list":
        for meta in store.list():
            print(f"{meta.artifact_id}@{meta.revision} [{meta.status}] kind={meta.kind} {meta.content_hash}")
    elif args.cmd == "get":
        artifact = store.get(args.artifact_id)
        print(json.dumps(artifact.metadata.to_dict(), ensure_ascii=False, indent=2))
        print("--- content ---")
        print(artifact.content, end="")
    elif args.cmd == "validate":
        errors = store.validate()
        if errors:
            for e in errors:
                print(f"  [error] {e}")
            raise SystemExit(1)
        print("artifact store consistent ✓")
    elif args.cmd == "write":
        if args.file and args.text:
            parser.error("use either --file or --text, not both")
        content = _read_text(args.file) if args.file else (args.text or "")
        meta = store.write(
            args.artifact_id,
            args.kind,
            content,
            status=args.status,
            depends_on=args.depends_on,
            supersedes=args.supersedes,
            updated_at=args.updated_at,
        )
        print(f"wrote {meta.artifact_id}@{meta.revision} [{meta.status}] {meta.content_hash}")
    elif args.cmd == "hash":
        print(content_hash(sys.stdin.read()))


if __name__ == "__main__":
    main()
