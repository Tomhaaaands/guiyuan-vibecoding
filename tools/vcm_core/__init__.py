"""Shared VCM authority and repository primitives."""
"""Shared authority primitives for the VCM modular monolith."""

MODULE_ID = "core"
CONTRACT_VERSION = "v1"

from .module_protocol import ModuleResult, blocked, complete, failed, ready  # noqa: F401,E402
