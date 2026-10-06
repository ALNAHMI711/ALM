from product_artifacts import ProductArtifact, ProductArtifactRegistry


def test_registry_resolves_product_artifact():
    registry = ProductArtifactRegistry(
        (
            ProductArtifact(
                product_id="yow-core",
                platform="android",
                version="0.1.0",
                storage_key="releases/yow-core.apk",
            ),
        )
    )

    artifact = registry.get("yow-core")
    assert artifact is not None
    assert artifact.platform == "android"
    assert artifact.storage_key == "releases/yow-core.apk"


def test_unknown_product_is_not_resolved():
    registry = ProductArtifactRegistry()
    assert registry.get("missing") is None


def test_registry_lists_products_deterministically():
    registry = ProductArtifactRegistry((
        ProductArtifact("yow-expansion", "android", "0.1.0", "packs/expansion.apk", "World Expansion", "content_pack"),
        ProductArtifact("yow-core", "android", "0.1.0", "releases/yow-core.apk", "YOW Core", "game"),
    ))
    assert [item.product_id for item in registry.all()] == ["yow-core", "yow-expansion"]
    assert registry.get("yow-expansion").kind == "content_pack"
    assert registry.get("yow-expansion").name == "World Expansion"
