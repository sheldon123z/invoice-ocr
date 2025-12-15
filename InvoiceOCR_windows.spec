# -*- mode: python ; coding: utf-8 -*-
# Windows 专用打包配置

a = Analysis(
    ['invoice_ocr_gui.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['invoice_ocr_sum', 'invoice_ocr_simple', 'ocr_api', 'openpyxl', 'openpyxl.styles'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='InvoiceOCR',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
