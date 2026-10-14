import copy

import validate_source as validator
from test_update_source import make_app


def valid_source():
    app = validator_source_app()
    return {
        "name": "Chi Source Personal",
        "identifier": "com.tsai97216.chisourcepersonal",
        "sourceURL": "https://example.com/apps.json",
        "subtitle": "Personal source",
        "description": "Test source",
        "website": "https://example.com",
        "iconURL": "https://example.com/icon.png",
        "featuredApps": [app["bundleIdentifier"]],
        "apps": [app],
        "news": [],
    }


def validator_source_app():
    return {
        "name": "Demo",
        "bundleIdentifier": "com.example.demo",
        "developerName": "Demo Dev",
        "subtitle": "Demo",
        "localizedDescription": "Demo app",
        "iconURL": "https://example.com/icon.png",
        "tintColor": "#123456",
        "category": "entertainment",
        "screenshots": [{"imageURL": "https://example.com/screenshot.png"}],
        "appPermissions": {"entitlements": [], "privacy": {}},
        "versions": [{
            "version": "1.0",
            "date": "2026-10-01",
            "localizedDescription": "Initial release",
            "downloadURL": "https://example.com/demo.ipa",
            "size": 123,
        }],
    }


def test_validate_valid_source():
    assert validator.validate_source_data(valid_source()) is True


def test_rejects_invalid_tint_color():
    source = copy.deepcopy(valid_source())
    source["apps"][0]["tintColor"] = "GGGGGG"
    assert validator.validate_source_data(source) is False


def test_rejects_invalid_version_date():
    source = copy.deepcopy(valid_source())
    source["apps"][0]["versions"][0]["date"] = "not-a-date"
    assert validator.validate_source_data(source) is False


def test_rejects_non_positive_size():
    source = copy.deepcopy(valid_source())
    source["apps"][0]["versions"][0]["size"] = 0
    assert validator.validate_source_data(source) is False


def test_rejects_invalid_screenshot_url():
    source = copy.deepcopy(valid_source())
    source["apps"][0]["screenshots"] = [{"imageURL": "http://example.com/image.png"}]
    assert validator.validate_source_data(source) is False


def test_rejects_duplicate_version_identity():
    source = copy.deepcopy(valid_source())
    source["apps"][0]["versions"].append(copy.deepcopy(source["apps"][0]["versions"][0]))
    assert validator.validate_source_data(source) is False


def test_rejects_duplicate_bundle_id():
    source = copy.deepcopy(valid_source())
    source["apps"].append(copy.deepcopy(source["apps"][0]))
    assert validator.validate_source_data(source) is False
