# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['invoice_ocr_gui.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'invoice_ocr_sum',
        'invoice_ocr_simple',
        'openpyxl',
        'openpyxl.styles',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='InvoiceOCR',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 设置为 False 以隐藏控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 可以设置应用图标路径
)

# macOS 应用包配置
app = BUNDLE(
    exe,
    name='InvoiceOCR.app',
    icon=None,
    bundle_identifier='com.invoiceocr.app',
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSHighResolutionCapable': 'True',
        'CFBundleName': 'Invoice OCR',
        'CFBundleDisplayName': 'Invoice OCR',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleVersion': '1.0.0',
    },
)
