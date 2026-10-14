import copy

import update_source as updater


def make_app(name="Demo", bundle_id="com.example.demo", screenshots=None, versions=None):
    return {
        "name": name,
        "bundleIdentifier": bundle_id,
        "developerName": "Demo Dev",
        "localizedDescription": "Demo app",
        "iconURL": "https://example.com/icon.png",
        "tintColor": "#123456",
        "category": "entertainment",
        "screenshots": screenshots or [],
        "appPermissions": {"entitlements": [], "privacy": {}},
        "versions": versions or [{
            "version": "1.0",
            "date": "2026-10-01",
            "localizedDescription": "Initial release",
            "downloadURL": "https://example.com/demo.ipa",
            "size": 123,
        }],
    }


def test_screenshot_formats_are_normalized():
    raw = make_app(screenshots={
        "iphone": ["https://example.com/one.png"],
        "ipad": [{"imageURL": "https://example.com/two.png", "width": 800}],
    })
    app = updater.normalize_app(raw, "Fixture")
    assert app["screenshots"] == [
        {"imageURL": "https://example.com/one.png"},
        {"imageURL": "https://example.com/two.png"},
    ]


def test_duplicate_bundle_ids_keep_first_source():
    first = {"name": "First", "apps": [make_app("First", "com.example.same")]}
    second = {"name": "Second", "apps": [make_app("Second", "com.example.same")]}
    apps, _ = updater.merge_catalogs([("FirstSource", first), ("SecondSource", second)])
    assert len(apps) == 1
    assert apps[0]["name"] == "First"


def test_build_source_creates_personal_metadata():
    catalog = {"apps": [make_app()]}
    source = updater.build_source([("Fixture", catalog)])
    assert source["name"] == "Chi Source Personal"
    assert source["identifier"] == "com.tsai97216.chisourcepersonal"
    assert source["featuredApps"] == ["com.example.demo"]
    assert len(source["apps"]) == 1


def test_spoofer_style_same_version_different_builds_are_kept():
    app = make_app(versions=[
        {
            "version": "0.431.1",
            "buildVersion": "0.734",
            "date": "2026-10-08T20:32:10+00:00",
            "localizedDescription": "Build 734",
            "downloadURL": "https://example.com/one.ipa",
            "size": 100,
        },
        {
            "version": "0.431.1",
            "buildVersion": "0.733",
            "date": "2026-10-07T19:14:28+00:00",
            "localizedDescription": "Build 733",
            "downloadURL": "https://example.com/two.ipa",
            "size": 101,
        },
    ])
    normalized = updater.normalize_app(app, "Fixture")
    assert len(normalized["versions"]) == 2


def test_invalid_source_entry_fails_loudly():
    bad = {"apps": [{"name": "Broken"}]}
    try:
        updater.merge_catalogs([("BrokenSource", bad)])
    except ValueError as exc:
        assert "bundleIdentifier" in str(exc)
    else:
        raise AssertionError("Expected malformed source entry to fail")
