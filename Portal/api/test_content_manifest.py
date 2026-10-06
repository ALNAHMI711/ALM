from content_manifest import ContentManifestRegistry, ContentPackRelease

SHA = "a" * 64

def test_manifest_resolves_latest_pack_release():
    registry = ContentManifestRegistry((
        ContentPackRelease("world", "yow-core", "1.0.0", "android", "packs/world-100.bin", SHA, 100),
        ContentPackRelease("world", "yow-core", "1.1.0", "android", "packs/world-110.bin", SHA, 120),
    ))
    assert registry.get("yow-core", "world").version == "1.1.0"
    assert registry.get("yow-core", "world", "1.0.0").size_bytes == 100

def test_manifest_does_not_cross_products():
    registry = ContentManifestRegistry((
        ContentPackRelease("world", "yow-core", "1.0.0", "android", "packs/world.bin", SHA, 100),
    ))
    assert registry.get("other-product", "world") is None

def test_manifest_rejects_unsafe_key_and_bad_checksum():
    try:
        ContentPackRelease("world", "yow-core", "1.0.0", "android", "../world.bin", SHA, 100)
        assert False
    except ValueError:
        pass
    try:
        ContentPackRelease("world", "yow-core", "1.0.0", "android", "packs/world.bin", "bad", 100)
        assert False
    except ValueError:
        pass
