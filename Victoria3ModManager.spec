# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=[],
    datas=[
        ("resources/prompts", "resources/prompts"),
        ("resources/translations", "resources/translations"),
        ("resources/icons", "resources/icons"),
        ("resources/styles", "resources/styles"),
    ],
    hiddenimports=["PySide6.QtSvg"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

# Never bundle a UCRT or ICU copied from another program found on the build
# PATH. Supported Windows versions provide these system DLLs. Shipping a
# mismatched copy can make PySide6 fail with "specified procedure not found".
a.binaries = TOC(
    item
    for item in a.binaries
    if not (
        item[0].lower() == "ucrtbase.dll"
        or item[0].lower().startswith("api-ms-win-crt-")
        or item[0].lower() == "icuuc.dll"
        or item[0].lower().startswith("icudt")
    )
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="Victoria3ModManager",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    version="resources/windows/version_info.txt",
    icon="resources/icons/app.ico",
)
