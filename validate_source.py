import json
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

FILENAME = "apps.json"
VALID_CATEGORIES = {
    "developer", "entertainment", "games", "lifestyle",
    "other", "photo-video", "social", "utilities",
}
HEX_COLOR_RE = re.compile(r"^(?:#)?[0-9A-Fa-f]{6}$")
REQUIRED_ROOT_FIELDS = {
    "name", "identifier", "sourceURL", "subtitle", "description",
    "website", "iconURL", "featuredApps", "apps", "news",
}
REQUIRED_APP_FIELDS = {
    "name", "bundleIdentifier", "developerName", "subtitle",
    "localizedDescription", "iconURL", "tintColor", "category",
    "screenshots", "versions", "appPermissions",
}
REQUIRED_VERSION_FIELDS = {
    "version", "date", "localizedDescription", "downloadURL", "size",
}


def valid_https_url(value):
    if not isinstance(value, str):
        return False
    try:
        parsed = urlparse(value)
        return parsed.scheme == "https" and bool(parsed.netloc)
    except ValueError:
        return False


def valid_date(value):
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def version_identity(version):
    return (version.get("version"), version.get("buildVersion", ""))


def validate_source_data(source):
    if not isinstance(source, dict):
        print("❌ Root must be an object")
        return False

    missing = REQUIRED_ROOT_FIELDS - set(source)
    if missing:
        print(f"❌ Missing root fields: {', '.join(sorted(missing))}")
        return False

    for field in ("name", "identifier", "subtitle", "description"):
        if not isinstance(source[field], str) or not source[field].strip():
            print(f"❌ Invalid root field: {field}")
            return False
    for field in ("sourceURL", "website", "iconURL"):
        if not valid_https_url(source[field]):
            print(f"❌ Invalid root URL: {field}")
            return False

    apps = source["apps"]
    if not isinstance(apps, list) or not apps:
        print("❌ apps must be a non-empty array")
        return False
    if not isinstance(source["featuredApps"], list) or not isinstance(source["news"], list):
        print("❌ featuredApps and news must be arrays")
        return False

    bundle_ids = set()
    for app in apps:
        if not isinstance(app, dict):
            print("❌ Every app entry must be an object")
            return False
        missing_fields = REQUIRED_APP_FIELDS - set(app)
        if missing_fields:
            print(f"❌ {app.get('name', 'Unknown')}: missing fields: {', '.join(sorted(missing_fields))}")
            return False

        for field in ("name", "bundleIdentifier", "developerName", "subtitle", "localizedDescription"):
            if not isinstance(app[field], str) or not app[field].strip():
                print(f"❌ Invalid app field: {app.get('name', 'Unknown')} / {field}")
                return False
        bundle_id = app["bundleIdentifier"]
        if bundle_id in bundle_ids:
            print(f"❌ Duplicate bundleIdentifier: {bundle_id}")
            return False
        bundle_ids.add(bundle_id)

        if not valid_https_url(app["iconURL"]):
            print(f"❌ {app['name']}: invalid iconURL")
            return False
        if not isinstance(app["tintColor"], str) or not HEX_COLOR_RE.fullmatch(app["tintColor"]):
            print(f"❌ {app['name']}: invalid tintColor")
            return False
        if app["category"] not in VALID_CATEGORIES:
            print(f"❌ {app['name']}: invalid category")
            return False

        screenshots = app["screenshots"]
        if not isinstance(screenshots, list):
            print(f"❌ {app['name']}: screenshots must be an array")
            return False
        for screenshot in screenshots:
            if not isinstance(screenshot, dict) or not valid_https_url(screenshot.get("imageURL")):
                print(f"❌ {app['name']}: invalid screenshot entry")
                return False

        permissions = app["appPermissions"]
        if not isinstance(permissions, dict):
            print(f"❌ {app['name']}: appPermissions must be an object")
            return False
        if not isinstance(permissions.get("entitlements", []), list):
            print(f"❌ {app['name']}: entitlements must be an array")
            return False
        if not isinstance(permissions.get("privacy", {}), dict):
            print(f"❌ {app['name']}: privacy must be an object")
            return False

        versions = app["versions"]
        if not isinstance(versions, list) or not versions:
            print(f"❌ {app['name']}: versions must be a non-empty array")
            return False
        seen_versions = set()
        for index, version in enumerate(versions):
            if not isinstance(version, dict):
                print(f"❌ {app['name']}: version {index} must be an object")
                return False
            missing_version_fields = REQUIRED_VERSION_FIELDS - set(version)
            if missing_version_fields:
                print(f"❌ {app['name']}: version {index} missing fields: {', '.join(sorted(missing_version_fields))}")
                return False
            if not isinstance(version["version"], str) or not version["version"].strip():
                print(f"❌ {app['name']}: invalid version string")
                return False
            if not valid_date(version["date"]):
                print(f"❌ {app['name']}: invalid version date {version['date']!r}")
                return False
            if not isinstance(version["localizedDescription"], str):
                print(f"❌ {app['name']}: invalid version description")
                return False
            url = version["downloadURL"]
            if not valid_https_url(url) or not url.lower().split("?", 1)[0].endswith(".ipa"):
                print(f"❌ {app['name']}: invalid IPA downloadURL")
                return False
            if type(version["size"]) is not int or version["size"] <= 0:
                print(f"❌ {app['name']}: invalid IPA size")
                return False
            identity = version_identity(version)
            if identity in seen_versions:
                print(f"❌ {app['name']}: duplicate version identity {identity}")
                return False
            seen_versions.add(identity)

    if set(source["featuredApps"]) != bundle_ids:
        print("❌ featuredApps does not match the app bundle identifiers")
        return False

    for item in source["news"]:
        if not isinstance(item, dict):
            print("❌ Every news entry must be an object")
            return False

    print(f"✅ Valid AltStore source: {len(apps)} apps")
    return True


def main():
    try:
        source = json.loads(Path(FILENAME).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"❌ Could not read {FILENAME}: {exc}")
        raise SystemExit(1)
    if not validate_source_data(source):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
