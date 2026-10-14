import json
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT = Path(__file__).resolve().parent
SOURCES_FILE = ROOT / "app_config.json"
OUTPUT_FILE = ROOT / "apps.json"
SOURCE_NAME = "Chi Source Personal"
SOURCE_IDENTIFIER = "com.tsai97216.chisourcepersonal"
SOURCE_URL = "https://raw.githubusercontent.com/tsai97216/chi-source-personal/main/apps.json"
SOURCE_WEBSITE = "https://github.com/tsai97216/chi-source-personal"
SOURCE_ICON = "https://raw.githubusercontent.com/tsai97216/chi-source-personal/main/source_icon.png"
VALID_CATEGORIES = {
    "developer", "entertainment", "games", "lifestyle",
    "other", "photo-video", "social", "utilities",
}
HEX_COLOR = re.compile(r"^#?[0-9a-fA-F]{6}$")


def create_session():
    retry = Retry(
        total=3,
        connect=3,
        read=3,
        status=3,
        backoff_factor=1,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
        respect_retry_after_header=True,
    )
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.headers.update({
        "User-Agent": "Chi-Source-Personal-Updater/1.0",
        "Accept": "application/json",
    })
    return session


def is_https_url(value):
    if not isinstance(value, str):
        return False
    try:
        parsed = urlparse(value)
        return parsed.scheme == "https" and bool(parsed.netloc)
    except ValueError:
        return False


def collect_screenshot_urls(value):
    """Normalize AltStore screenshot formats into a list of HTTPS image URLs."""
    found = []

    def visit(item):
        if isinstance(item, str):
            if is_https_url(item):
                found.append(item)
        elif isinstance(item, list):
            for child in item:
                visit(child)
        elif isinstance(item, dict):
            if isinstance(item.get("imageURL"), str):
                visit(item["imageURL"])
            else:
                for key in ("iphone", "ipad", "images", "screenshots"):
                    if key in item:
                        visit(item[key])

    visit(value)
    return list(dict.fromkeys(found))


def normalize_version(raw, app_name):
    if not isinstance(raw, dict):
        raise ValueError(f"{app_name}: version entry is not an object")

    version = raw.get("version")
    date = raw.get("date")
    download_url = raw.get("downloadURL")
    size = raw.get("size")

    if not isinstance(version, str) or not version.strip():
        raise ValueError(f"{app_name}: version has no version string")
    if not isinstance(date, str) or not date.strip():
        raise ValueError(f"{app_name} {version}: version has no date")
    try:
        datetime.fromisoformat(date.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{app_name} {version}: invalid date {date!r}") from exc
    if not is_https_url(download_url):
        raise ValueError(f"{app_name} {version}: invalid downloadURL")
    if not download_url.lower().split("?", 1)[0].endswith(".ipa"):
        raise ValueError(f"{app_name} {version}: downloadURL is not an IPA")
    if isinstance(size, str) and size.isdigit():
        size = int(size)
    if type(size) is not int or size <= 0:
        raise ValueError(f"{app_name} {version}: invalid IPA size")

    normalized = dict(raw)
    normalized["version"] = version.strip()
    normalized["date"] = date
    normalized["downloadURL"] = download_url
    normalized["size"] = size
    description = normalized.get("localizedDescription", "")
    normalized["localizedDescription"] = description if isinstance(description, str) else str(description)
    return normalized


def normalize_app(raw, source_name):
    if not isinstance(raw, dict):
        raise ValueError(f"{source_name}: app entry is not an object")

    name = raw.get("name")
    bundle_id = raw.get("bundleIdentifier")
    icon_url = raw.get("iconURL")
    if not isinstance(name, str) or not name.strip():
        raise ValueError(f"{source_name}: app has no name")
    if not isinstance(bundle_id, str) or not bundle_id.strip():
        raise ValueError(f"{source_name} / {name}: app has no bundleIdentifier")
    if not is_https_url(icon_url):
        raise ValueError(f"{source_name} / {name}: invalid iconURL")

    raw_versions = raw.get("versions")
    if not isinstance(raw_versions, list) or not raw_versions:
        raise ValueError(f"{source_name} / {name}: no versions")
    versions = [normalize_version(item, name) for item in raw_versions]

    tint = raw.get("tintColor", "#777777")
    if not isinstance(tint, str) or not HEX_COLOR.fullmatch(tint):
        tint = "#777777"

    category = raw.get("category", "other")
    if category not in VALID_CATEGORIES:
        category = "other"

    screenshots = [
        {"imageURL": url}
        for url in collect_screenshot_urls(raw.get("screenshots", []))
    ]

    permissions = raw.get("appPermissions")
    if not isinstance(permissions, dict):
        permissions = {}
    entitlements = permissions.get("entitlements", [])
    privacy = permissions.get("privacy", {})
    if not isinstance(entitlements, list):
        entitlements = []
    if not isinstance(privacy, dict):
        privacy = {}

    app = dict(raw)
    app.update({
        "name": name.strip(),
        "bundleIdentifier": bundle_id.strip(),
        "developerName": raw.get("developerName") or source_name,
        "subtitle": raw.get("subtitle") or name.strip(),
        "localizedDescription": raw.get("localizedDescription") or "",
        "iconURL": icon_url,
        "tintColor": tint,
        "category": category,
        "screenshots": screenshots,
        "appPermissions": {
            **permissions,
            "entitlements": entitlements,
            "privacy": privacy,
        },
        "versions": versions,
    })
    return app


def merge_catalogs(catalogs, excluded_bundle_ids=None):
    """Merge (source_name, source_json) pairs; the first bundle ID wins."""
    excluded_bundle_ids = set(excluded_bundle_ids or [])
    excluded_bundle_ids.add("com.spooferpro.pokemongo")
    apps = []
    seen_bundle_ids = set()
    news = []
    seen_news = set()

    for source_name, catalog in catalogs:
        if not isinstance(catalog, dict) or not isinstance(catalog.get("apps"), list):
            raise ValueError(f"{source_name}: source JSON has no apps array")

        for raw_app in catalog["apps"]:
            app = normalize_app(raw_app, source_name)
            bundle_id = app["bundleIdentifier"]
            if bundle_id in excluded_bundle_ids:
                print(f"Excluded by configuration: {app['name']} ({bundle_id})")
                continue
            if bundle_id in seen_bundle_ids:
                print(f"⚠️ Duplicate bundle ID skipped: {app['name']} ({bundle_id})")
                continue
            seen_bundle_ids.add(bundle_id)
            apps.append(app)

        raw_news = catalog.get("news", [])
        if isinstance(raw_news, list):
            for item in raw_news:
                if not isinstance(item, dict):
                    continue
                app_id = item.get("appID")
                if app_id and app_id not in seen_bundle_ids:
                    continue
                key = (
                    item.get("identifier"),
                    item.get("title"),
                    item.get("date"),
                    app_id,
                )
                if key not in seen_news:
                    seen_news.add(key)
                    news.append(item)

    if not apps:
        raise ValueError("No apps were collected from the configured sources")

    return apps, news


def build_source(catalogs, excluded_bundle_ids=None):
    apps, news = merge_catalogs(catalogs, excluded_bundle_ids)
    return {
        "name": SOURCE_NAME,
        "identifier": SOURCE_IDENTIFIER,
        "sourceURL": SOURCE_URL,
        "subtitle": "個人精選的 ACG、小眾 App 與興趣工具",
        "description": (
            "Chi Source Personal 是個人興趣向的 AltStore / SideStore Source。"
            "App 資訊與版本由各專案的公開來源同步，請留意各 App 的使用條款與權限。"
        ),
        "website": SOURCE_WEBSITE,
        "iconURL": SOURCE_ICON,
        "featuredApps": [app["bundleIdentifier"] for app in apps],
        "apps": apps,
        "news": news,
    }


def load_catalogs(session, sources):
    catalogs = []
    for source in sources:
        name = source.get("name")
        url = source.get("url")
        if not isinstance(name, str) or not name.strip() or not is_https_url(url):
            raise ValueError(f"Invalid source configuration: {source!r}")
        print(f"⬇️ Fetching {name}: {url}")
        response = session.get(url, timeout=25)
        response.raise_for_status()
        try:
            data = response.json()
        except ValueError as exc:
            raise ValueError(f"{name}: response is not valid JSON") from exc
        if not isinstance(data, dict) or not isinstance(data.get("apps"), list):
            raise ValueError(f"{name}: response does not contain an apps array")
        catalogs.append((name, data))
        print(f"   Found {len(data['apps'])} app entries")
    return catalogs


def main():
    try:
        config = json.loads(SOURCES_FILE.read_text(encoding="utf-8"))
        sources = config.get("sources") if isinstance(config, dict) else None
        if not isinstance(sources, list) or not sources:
            raise ValueError("sources.json must contain a non-empty sources array")

        catalogs = load_catalogs(create_session(), sources)
        excluded_bundle_ids = config.get("excludedBundleIdentifiers", [])
        if not isinstance(excluded_bundle_ids, list) or not all(isinstance(item, str) and item.strip() for item in excluded_bundle_ids):
            raise ValueError("excludedBundleIdentifiers must be an array of non-empty strings")
        source = build_source(catalogs, excluded_bundle_ids)
        OUTPUT_FILE.write_text(
            json.dumps(source, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"✅ Wrote {len(source['apps'])} apps to {OUTPUT_FILE.name}")
    except Exception as exc:
        print(f"❌ Source sync failed: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
