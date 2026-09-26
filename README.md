**English** | [한국어](README_KO.md)

# Victoria 3 Mod Manager (V3MM)

Victoria 3 Mod Manager is a Windows desktop application for safely preparing, translating, validating, updating, and installing Victoria 3 mod localization files.

![Victoria 3 Mod Manager v2.1.2](docs/images/v2.1.2-home.png)

## Download

- [Download the current Windows executable](download/Victoria3ModManager.exe)
- [Open GitHub Releases](https://github.com/blor123/Victoria-3-Mod-Translation-Tool/releases/latest)

The packaged executable does not require Python. User settings and projects remain in `%LOCALAPPDATA%\Victoria3ModManager` when the executable is replaced.

## v2.1.2

- Moved **Translation Update** directly below **Quick Translation** in the sidebar.
- Added support for Google AI Studio `AQ.` authorization keys through the Gemini Interactions API.
- Updated the default model to `gemini-3.8-flash` and automatically migrates the old v2.1.0 default.
- Improved messages for authentication and Google Cloud project-permission errors.
- Safely ignores late update-check callbacks after the application starts closing.
- Passed 60 automated regression tests and Windows executable smoke testing.

![Translation Update](docs/images/v2.1.2-translation-update.png)

## Major features

### Quick and manual translation workflows

- Select one or more YML files, localization folders, or mod folders.
- Preserve the localization directory layout and original source files.
- Convert filename suffixes and localization headers for five target languages.
- Create AI-ready ZIP packages and safely install returned translations.
- Preview inputs, edit translation instructions, detect duplicates, and back up files before replacement.

### Gemini one-click translation

- Bring your own Google Gemini API key, stored in Windows Credential Manager rather than `config.json`.
- Translate localization files and update only `NEW` or `CHANGED` entries.
- Protect Victoria 3 variables and formatting tokens during translation.
- Use automatic batching, retry handling, cancellation, and partial-failure preservation.
- Build translations in a separate preview directory without modifying source localization files.

### Translation updates and projects

- Compare localization snapshots and classify `NEW`, `CHANGED`, `DELETED`, and `UNCHANGED` entries.
- Merge translated updates while preserving existing and deleted-source translations.
- Create, edit, and remove reusable translation projects.
- Validate returned ZIP packages against the package manifest, keys, and protected tokens.

### Conflict analysis

- Read-only local analysis for identical paths, localization keys, Victoria 3 definitions, and `replace_path` overlap.
- Evidence-oriented side-by-side details and JSON report export.
- Optional Gemini analysis sends only selected conflict snippets and uses a local result cache.

### Safety and interface

- Blocks Zip Slip, symbolic links, encrypted archives, duplicate targets, and excessive extraction size.
- Supports Korean, English, Simplified Chinese, Traditional Chinese, and Japanese UI languages.
- Includes projects, recent activity, notification center, GitHub update checks, Dark Victorian UI, and DPI-aware layouts.
- Does not modify Steam or Paradox Launcher configuration.

## Development

Python 3.11 or newer is recommended.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

Run tests:

```powershell
python -m unittest discover -s tests -v
```

Build the Windows executable:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_windows.ps1
```

## Security

V3MM does not request ChatGPT login credentials, cookies, or session tokens. A user-supplied Gemini key is stored only in Windows Credential Manager. Never publish an API key in an issue, screenshot, log, or repository.

## Author

Created by KakaoL — [Steam profile](https://steamcommunity.com/id/KakaoLV3MM/)
