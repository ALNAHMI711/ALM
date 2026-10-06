from product_artifacts import ProductArtifact, ProductArtifactRegistry


def test_registry_resolves_product_artifact():
    registry = ProductArtifactRegistry(
        (
            ProductArtifact(
                product_id="yow-core",
                platform="android",
                version="0.1.0",
                storage_url="https://storage.example/yow-core.apk",
            ),
        )
    )

    artifact = registry.get("yow-core")
    assert artifact is not None
    assert artifact.platform == "android"


def test_unknown_product_is_not_resolved():
    registry = ProductArtifactRegistry()
    assert registry.get("missing") is None
