# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from pathlib import Path

# --- 1. 定义源代码的根目录 ---
project_root = Path(SPECPATH)
source_root = project_root / 'src'
print(f"将源代码根目录添加到搜索路径: {source_root}")


# --- 2. 自动检测 Conda 环境并准备核心 DLLs ---
core_binaries = []
if 'conda' in sys.executable:
    conda_env_path = Path(sys.executable).parent
    print(f"检测到 Conda 环境, 路径: {conda_env_path}")
    
    required_dlls = ['python311.dll', 'vcruntime140.dll']
    
    for dll in required_dlls:
        dll_path = conda_env_path / dll
        if dll_path.exists():
            print(f"  [OK] 找到 {dll}, 将其添加到打包列表。")
            core_binaries.append((str(dll_path), '.'))
        else:
            print(f"  [警告] 未能在 Conda 环境根目录找到 {dll}!")

# --- 3. 定义平台特定的数据文件 ---
platform_datas = []
if sys.platform == "win32":
    print("检测到 Windows 系统, 将打包 'vendor/ffmpeg_win'")
    platform_datas.append(('vendor/ffmpeg_win', 'vendor/ffmpeg_win'))
elif sys.platform == "darwin":
    print("检测到 macOS 系统, 将打包 'vendor/ffmpeg_mac'")
    platform_datas.append(('vendor/ffmpeg_mac', 'vendor/ffmpeg_mac'))

# --- 4. 定义所有平台都需要的数据文件 ---
common_datas = [
    ('assets/help', 'assets/help'),
    ('assets/icons', 'assets/icons'),
    ('README.md', '.')
]

# --- 5. 合并所有数据和二进制文件 ---
all_datas = platform_datas + common_datas

# --- 6. PyInstaller 标准配置 ---
block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=[str(source_root)],
    binaries=core_binaries,
    datas=all_datas,
    hiddenimports=['PySide6.QtSvg'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PyQt6'],  # <-- 【核心修改】在这里排除 PyQt6
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe_name = '句子粗剪器'

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=exe_name,
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
    icon='assets/icons/paper-cut.png',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=exe_name,
)