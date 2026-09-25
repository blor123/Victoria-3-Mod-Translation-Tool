# Victoria 3 Mod Manager (V3MM)

Victoria 3 Mod Manager, or **V3MM**, is a Windows utility designed to make
Victoria 3 mod localization and management easier.

V3MM provides a simple workflow for preparing localization files for AI-assisted
translation and applying the translated files back to your mod.

(Victoria 3 Mod Translation Tool)
---

## Features

### Translation Package

Prepare Victoria 3 localization files for translation.

- Select individual YML files or localization folders
- Preserve the original localization structure
- Convert translation package filenames when necessary
- Prepare localization files for Korean translation
- Create a ZIP package ready to upload to ChatGPT
- Copy the recommended translation instructions

### Apply Translation

Apply translated localization files returned by ChatGPT.

- Import translated ZIP packages
- Automatically locate localization files
- Safely extract ZIP files
- Detect duplicate targets
- Backup existing files before replacement
- Install translated localization files to the selected location

### Multilingual Interface

V3MM supports the following interface languages:

- 한국어
- English
- 简体中文
- 繁體中文
- 日本語

---

## Translation Workflow

V3MM does **not** directly connect to the ChatGPT API.

Instead, it provides a simple file-based workflow:

1. Select the Victoria 3 localization files in V3MM.
2. Create a translation package.
3. Upload the generated ZIP file to ChatGPT.
4. Translate the localization files using the provided V3MM translation instructions.
5. Download the translated ZIP file.
6. Import the ZIP file back into V3MM.
7. V3MM applies the translated files to the selected location.

This approach allows ChatGPT users to use their existing ChatGPT environment
without requiring an OpenAI API key.

---

## Supported Platform

- Windows 10
- Windows 11

V3MM is currently designed for Windows.

---

## Installation

1. Download the latest version from **Releases**.
2. Extract the downloaded archive if necessary.
3. Run `V3MM.exe`.

No Python installation is required for the packaged version.

---

## Important

Always keep a backup of important mod files.

V3MM includes safety features such as backup creation and safe ZIP extraction,
but mod files can vary significantly between projects.

---

## Roadmap

### v1.2

- Improved translation workflow
- Drag & Drop support
- Localization language declaration handling
- Translation prompt management
- Multilingual V3MM interface
- Improved translation package summary

### Future

Planned features include:

- Translation validation
- Translation project management
- Mod conflict analysis
- Load-order analysis and recommendations
- Update system

The roadmap may change as development progresses.

---

## Author

**Created by KakaoL**

Steam Profile:  
https://steamcommunity.com/id/KakaoLV3MM/
