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



def test_allowed_bundle_ids_filter_unconfigured_apps():
    catalog = {
        "apps": [
            make_app("Keep", "com.example.keep"),
            make_app("Skip", "com.example.skip"),
        ]
    }
    apps, _ = updater.merge_catalogs(
        [("Fixture", catalog)],
        allowed_bundle_ids={"com.example.keep"},
    )
    assert [app["name"] for app in apps] == ["Keep"]

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

class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, payload):
        self.payload = payload

    def get(self, url, timeout):
        assert url.endswith("/releases?per_page=30")
        assert timeout == 25
        return FakeResponse(self.payload)


def test_github_release_catalog_uses_ipa_asset():
    config = {
        "name": "Example App",
        "bundleID": "com.example.app",
        "author": "Example",
        "source_name": "Example Releases",
        "github_repo": "example/app",
        "icon": "https://example.com/icon.png",
        "subtitle": "Example subtitle",
        "desc": "Example description",
        "color": "123456",
        "category": "utilities",
        "asset_keywords": ["example"],
    }
    releases = [{
        "draft": False,
        "prerelease": False,
        "tag_name": "v1.2.3",
        "published_at": "2026-10-01T12:00:00Z",
        "body": "Release notes",
        "assets": [
            {
                "name": "ExampleApp.ipa",
                "browser_download_url": "https://github.com/example/app/releases/download/v1.2.3/ExampleApp.ipa",
                "size": 12345,
            },
            {
                "name": "checksums.txt",
                "browser_download_url": "https://github.com/example/app/releases/download/v1.2.3/checksums.txt",
                "size": 120,
            },
        ],
    }]
    name, catalog = updater.load_github_release_catalog(FakeSession(releases), config)
    assert name == "Example Releases"
    app = catalog["apps"][0]
    assert app["bundleIdentifier"] == "com.example.app"
    assert app["versions"][0]["version"] == "1.2.3"
    assert app["versions"][0]["buildVersion"] == "v1.2.3"
    assert app["versions"][0]["downloadURL"].endswith("ExampleApp.ipa")
    assert app["versions"][0]["size"] == 12345


def test_github_release_catalog_fails_without_ipa():
    config = {
        "name": "Example App",
        "bundleID": "com.example.app",
        "github_repo": "example/app",
        "asset_keywords": ["example"],
    }
    releases = [{
        "draft": False,
        "prerelease": False,
        "tag_name": "v1.0",
        "published_at": "2026-10-01T12:00:00Z",
        "assets": [{
            "name": "source.zip",
            "browser_download_url": "https://github.com/example/app/releases/download/v1.0/source.zip",
            "size": 123,
        }],
    }]
    try:
        updater.load_github_release_catalog(FakeSession(releases), config)
    except ValueError as exc:
        assert "no public release" in str(exc)
    else:
        raise AssertionError("Expected missing IPA release to fail")

