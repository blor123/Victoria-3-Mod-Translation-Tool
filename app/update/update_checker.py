import json
import re
import urllib.request
from dataclasses import dataclass

from app.constants import GITHUB_OWNER, GITHUB_REPOSITORY


def version_tuple(value: str) -> tuple[int, ...]:
    match = re.fullmatch(r"v?(\d+(?:\.\d+)*)", value.strip())
    if not match: raise ValueError("Invalid semantic version")
    return tuple(map(int, match.group(1).split(".")))


@dataclass(frozen=True)
class UpdateInfo:
    version: str
    url: str
    notes: str = ""


def check_for_update(current_version: str, timeout: float = 5.0, opener=urllib.request.urlopen) -> UpdateInfo | None:
    if not GITHUB_OWNER or not GITHUB_REPOSITORY: return None
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPOSITORY}/releases/latest"
    request = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "V3MM-UpdateChecker"})
    with opener(request, timeout=timeout) as response: payload = json.loads(response.read().decode("utf-8"))
    if payload.get("draft") or payload.get("prerelease"): return None
    latest = str(payload["tag_name"])
    if version_tuple(latest) <= version_tuple(current_version): return None
    return UpdateInfo(latest.removeprefix("v"), str(payload["html_url"]), str(payload.get("body", ""))[:2000])
