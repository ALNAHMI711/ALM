import pytest

from artifact_policy import ArtifactPolicy, ArtifactPolicyError, validate_artifact_policy


def test_paid_artifact_cannot_be_public_github_asset():
    with pytest.raises(ArtifactPolicyError):
        validate_artifact_policy(
            ArtifactPolicy(
                paid=True,
                storage_url="https://storage.example/yow.apk",
                public_github_asset=True,
            )
        )


def test_paid_artifact_requires_absolute_storage_url():
    with pytest.raises(ArtifactPolicyError):
        validate_artifact_policy(
            ArtifactPolicy(paid=True, storage_url="/downloads/yow.apk")
        )


def test_private_paid_artifact_is_allowed():
    validate_artifact_policy(
        ArtifactPolicy(
            paid=True,
            storage_url="https://storage.example/yow.apk",
            public_github_asset=False,
        )
    )
