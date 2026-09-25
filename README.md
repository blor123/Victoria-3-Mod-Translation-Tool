[English](README.md) | [한국어](README_KO.md)

# Victoria 3 Mod Translation Tool & Manager (V3MM)

**Victoria 3 Mod Translation Tool & Manager (V3MM)** is a Windows application for preparing, translating, and managing Victoria 3 mod localization files.

V3MM provides a file-based workflow for AI/ChatGPT-assisted translation. It packages localization files into a ZIP archive for translation, then imports the translated ZIP and applies the files back to the mod. V3MM does not translate files by itself and does not connect directly to the OpenAI API or ChatGPT API.

[Download the latest release](https://github.com/blor123/Victoria-3-Mod-Translation-Tool/releases/latest)

![V3MM interface](https://github.com/user-attachments/assets/f30cfdd2-c88c-467d-8b99-702e565ffe8e)

## Features

### Translation Package

Prepare Victoria 3 localization files for translation.

- Select individual YML files, multiple YML files, or folders containing localization files
- Preserve the Victoria 3 `localization/korean` directory structure
- Convert `_english.yml` filenames to `_korean.yml` when required
- Change the copied package's `l_english:` declaration to `l_korean:` while preserving the original source files
- Preview the target YML files and remove duplicate selections
- Create a translation-ready ZIP package
- View, edit, reset, and copy the provided translation instructions

### Apply Translation

Import and apply translated files.

- Import translated ZIP packages regardless of their archive name or top-level wrapper folder
- Locate translated localization files automatically
- Safely extract ZIP files, with protections against unsafe paths and unsupported archives
- Detect duplicate installation targets before applying files
- Preview files before installation
- Back up existing files before replacement
- Choose whether to back up and overwrite, overwrite, skip, or cancel when files already exist

### Multilingual Interface

V3MM supports these interface languages:

- 한국어
- English
- 简体中文
- 繁體中文
- 日本語

The selected interface language is saved and restored when V3MM is reopened.

## ChatGPT Translation Workflow

V3MM is **not** connected to the OpenAI API or ChatGPT API. It does not request or store an OpenAI API key, ChatGPT login, cookie, or session token.

The standard workflow is:

1. Select Victoria 3 localization files in V3MM.
2. Create a translation package.
3. Upload the generated ZIP file to ChatGPT.
4. Translate the files using the translation instructions provided by V3MM.
5. Download the translated ZIP file.
6. Import the ZIP file back into V3MM.
7. Review and apply the translated files.

You can use your existing ChatGPT environment, so no separate OpenAI API key is required.

## Installation

V3MM supports **Windows 10** and **Windows 11**.

1. Open the [Releases page](https://github.com/blor123/Victoria-3-Mod-Translation-Tool/releases).
2. Open the latest release.
3. Download the packaged `.exe` file under **Assets**.
4. Run the downloaded file.

The packaged executable includes the required runtime. You do not need to install Python.

> Keep backups of important mod files. V3MM includes backup and safe-extraction features, but mod layouts can vary between projects.

## Roadmap

### Current release: v1.2.0

- Streamlined translation-package and apply-translation pages
- Drag-and-drop file and folder selection
- Localization language declaration handling
- Translation prompt management
- Multilingual interface
- Translation target preview and package summary
- Existing safety checks, duplicate detection, and backup options

### Future plans

The following items are planned and are not currently available:

- Translation validation
- Translation project management
- Mod conflict analysis
- Load-order analysis and recommendations
- Update system

The roadmap may change as development progresses.

## Author

**Created by KakaoL**

Steam Profile: [https://steamcommunity.com/id/KakaoLV3MM/](https://steamcommunity.com/id/KakaoLV3MM/)
