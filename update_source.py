import argparse
import json
import re
import sys
from datetime import datetime
from zoneinfo import ZoneInfo
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



APP_TABLE_START = "<!-- AUTO-UPDATE-APPS:START -->"
APP_TABLE_END = "<!-- AUTO-UPDATE-APPS:END -->"
STATUS_TIMES_START = "<!-- AUTO-UPDATE-STATUS-TIMES:START -->"
STATUS_TIMES_END = "<!-- AUTO-UPDATE-STATUS-TIMES:END -->"


def now_taiwan():
    return datetime.now(ZoneInfo("Asia/Taipei")).strftime("%Y-%m-%d %H:%M:%S")


def get_readme_status_times(readme):
    match = re.search(
        re.escape(STATUS_TIMES_START) + r"\s*<!--\s*(\{.*?\})\s*-->\s*" + re.escape(STATUS_TIMES_END),
        readme,
        flags=re.DOTALL,
    )
    if not match:
        return {}
    try:
        data = json.loads(match.group(1))
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def update_readme(apps, old_apps, config):
    path = ROOT / "README.md"
    readme = path.read_text(encoding="utf-8") if path.exists() else "# Chi Source Personal\n"
    checked_at = now_taiwan()
    previous_content = re.search(r"最近內容更新：\s*\**\s*(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", readme)
    content_changed = json.dumps(apps, ensure_ascii=False, sort_keys=True) != json.dumps(old_apps, ensure_ascii=False, sort_keys=True)
    content_updated_at = checked_at if content_changed else (previous_content.group(1) if previous_content else "尚未更新")
    previous_times = get_readme_status_times(readme)
    old_by_name = {app.get("name"): app for app in old_apps if isinstance(app, dict)}
    app_meta = {item.get("name"): item for item in config.get("apps", []) if isinstance(item, dict)}
    status_times = {}
    rows = ["| App | 原倉庫 | 狀態 | 最新版本 | 版本日期 | 上次更新 |", "| --- | --- | --- | --- | --- | --- |"]

    for app in apps:
        name = app.get("name", "Unknown")
        meta = app_meta.get(name, {})
        author = meta.get("author") or app.get("developerName", "Unknown")
        url = meta.get("repo_url", "")
        app_link = f"[{name}]({url})" if url else name
        latest = (app.get("versions") or [{}])[0]
        old = old_by_name.get(name)
        old_latest = ((old or {}).get("versions") or [{}])[0]
        old_version = (old_latest.get("version"), old_latest.get("buildVersion", ""))
        new_version_identity = (latest.get("version"), latest.get("buildVersion", ""))
        new_version = latest.get("version", "N/A")
        previous_time = previous_times.get(name)
        try:
            recent = previous_time and 0 <= (
                datetime.strptime(checked_at, "%Y-%m-%d %H:%M:%S")
                - datetime.strptime(previous_time, "%Y-%m-%d %H:%M:%S")
            ).total_seconds() < 86400
        except (TypeError, ValueError):
            recent = False
        if old_version != new_version_identity:
            status = "**Updated**"
            status_times[name] = checked_at
        elif recent:
            status = "**Updated**"
            status_times[name] = previous_time
        else:
            status = "Unchanged"
        update_time = f"**{status_times[name]}**" if name in status_times else (latest.get("date") or "N/A")
        rows.append(f"| **{app_link}** | {author} | {status} | {new_version} | {latest.get('date', 'N/A')} | {update_time} |")

    table = "\n".join([
        APP_TABLE_START,
        "## Apps 更新狀態",
        "",
        f"- **最近自動檢查：** {checked_at}（台灣時間）",
        f"- **最近內容更新：** {content_updated_at}（台灣時間）",
        "",
        *rows,
        "",
        APP_TABLE_END,
    ])
    if APP_TABLE_START in readme and APP_TABLE_END in readme:
        left = readme.index(APP_TABLE_START)
        right = readme.index(APP_TABLE_END, left) + len(APP_TABLE_END)
        readme = readme[:left] + table + readme[right:]
    else:
        readme = readme.rstrip() + "\n\n" + table + "\n"

    status_block = "\n".join([
        STATUS_TIMES_START,
        f"<!-- {json.dumps(status_times, ensure_ascii=False, sort_keys=True)} -->",
        STATUS_TIMES_END,
    ])
    if STATUS_TIMES_START in readme and STATUS_TIMES_END in readme:
        left = readme.index(STATUS_TIMES_START)
        right = readme.index(STATUS_TIMES_END, left) + len(STATUS_TIMES_END)
        readme = readme[:left] + status_block + readme[right:]
    else:
        readme = readme.rstrip() + "\n\n" + status_block + "\n"
    path.write_text(readme, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Update Chi Source Personal")
    parser.add_argument("--app", help="Only update the specified app. Omit or use 'all' to update all apps.")
    args = parser.parse_args()

    try:
        config = json.loads(SOURCES_FILE.read_text(encoding="utf-8"))
        app_configs = config.get("apps") if isinstance(config, dict) else None
        if not isinstance(app_configs, list) or not app_configs or not all(isinstance(app, dict) for app in app_configs):
            raise ValueError("app_config.json must contain a non-empty apps array")

        sources = []
        seen_source_urls = set()
        for app_config in app_configs:
            source_name = app_config.get("source_name")
            source_url = app_config.get("source_url")
            if not isinstance(source_name, str) or not source_name.strip() or not is_https_url(source_url):
                raise ValueError(f"Invalid source configuration for {app_config.get('name', 'Unknown')}")
            if source_url not in seen_source_urls:
                seen_source_urls.add(source_url)
                sources.append({"name": source_name, "url": source_url})

        catalogs = load_catalogs(create_session(), sources)
        source = build_source(catalogs)
        old_source = {}
        if OUTPUT_FILE.exists():
            try:
                old_source = json.loads(OUTPUT_FILE.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                old_source = {}
        old_apps_for_status = old_source.get("apps", []) if isinstance(old_source, dict) else []

        if args.app and args.app.lower() != "all":
            existing = {}
            if OUTPUT_FILE.exists():
                try:
                    existing = json.loads(OUTPUT_FILE.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    existing = {}
            old_apps = existing.get("apps", []) if isinstance(existing, dict) else []
            match = next(
                (app for app in source["apps"]
                 if app.get("name", "").casefold() == args.app.casefold()
                 or app.get("bundleIdentifier", "").casefold() == args.app.casefold()),
                None,
            )
            if match is None:
                raise ValueError(f"Unknown app: {args.app}")
            merged = list(old_apps) if isinstance(old_apps, list) else []
            index = next(
                (i for i, app in enumerate(merged)
                 if isinstance(app, dict) and (
                     app.get("bundleIdentifier") == match.get("bundleIdentifier")
                     or app.get("name") == match.get("name")
                 )),
                None,
            )
            if index is None:
                merged.append(match)
            else:
                merged[index] = match
            source["apps"] = merged
            source["featuredApps"] = [app["bundleIdentifier"] for app in merged if isinstance(app, dict)]
            if isinstance(existing, dict):
                source["news"] = existing.get("news", source.get("news", []))

        OUTPUT_FILE.write_text(
            json.dumps(source, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        update_readme(source["apps"], old_apps_for_status, config)
        print(f"✅ Wrote {len(source['apps'])} apps to {OUTPUT_FILE.name}")
    except Exception as exc:
        print(f"❌ Source sync failed: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
