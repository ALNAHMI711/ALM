"""Artifact policy for commercial YOW releases."""

from __future__ import annotations

from dataclasses import dataclass


class ArtifactPolicyError(ValueError):
    """Raised when an artifact violates paid-release policy."""


@dataclass(frozen=True)
class ArtifactPolicy:
    paid: bool
    storage_url: str
    public_github_asset: bool = False


def validate_artifact_policy(policy: ArtifactPolicy) -> None:
    if not policy.storage_url.startswith(("https://", "http://")):
        raise ArtifactPolicyError("artifact storage URL must be absolute")
    if policy.paid and policy.public_github_asset:
        raise ArtifactPolicyError("paid artifacts must not be public GitHub assets")
