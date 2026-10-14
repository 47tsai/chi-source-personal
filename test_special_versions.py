from update_source import collect_screenshot_urls, normalize_version


def test_nested_screenshot_objects_and_strings_are_collected():
    value = {
        "iphone": [
            "https://example.com/a.png",
            {"imageURL": "https://example.com/b.png", "width": 300},
        ],
        "ipad": [],
    }
    assert collect_screenshot_urls(value) == [
        "https://example.com/a.png",
        "https://example.com/b.png",
    ]


def test_version_keeps_optional_metadata():
    raw = {
        "version": "2.0",
        "buildVersion": "200",
        "date": "2026-10-10T10:00:00Z",
        "localizedDescription": "Update",
        "downloadURL": "https://example.com/app.ipa",
        "size": 500,
        "minOSVersion": "15.0",
    }
    result = normalize_version(raw, "Demo")
    assert result["buildVersion"] == "200"
    assert result["minOSVersion"] == "15.0"
