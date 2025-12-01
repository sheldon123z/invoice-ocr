# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['invoice_ocr_gui.py'],
    pathex=[],
    binaries=[('/opt/homebrew/bin/pdftoppm', 'bin')],
    datas=[],
    hiddenimports=['invoice_ocr_sum', 'invoice_ocr_simple', 'openpyxl', 'openpyxl.styles'],
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
    [],
    exclude_binaries=True,
    name='InvoiceOCR',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='InvoiceOCR',
)
app = BUNDLE(
    coll,
    name='InvoiceOCR.app',
    icon=None,
    bundle_identifier='com.invoiceocr.app',
)
