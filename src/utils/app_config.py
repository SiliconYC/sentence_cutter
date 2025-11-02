# path: src/utils/app_config.py

# ◔ 说明: 应用程序的全局公共配置模块。
#          所有硬编码的路径、名称和设置都应在此处统一定义，便于维护。

import sys
from pathlib import Path

# --- 应用程序元信息 ---
APP_NAME = "句子粗剪器"
CONFIG_FILENAME = "sentence_cutter_config.json"

# --- 平台检测 ---
IS_MACOS = sys.platform == 'darwin'

# --- 资源路径 ---
ICON_PATH = "assets/icons/paper-cut.png"

# --- 项目结构 ---
SOURCE_DIR_NAME = "01_Source"
INTERMEDIATE_DIR_NAME = "02_Intermediate"
CLIPS_DIR_NAME = "03_Clips"
OUTPUT_DIR_NAME = "04_Output"

PROJECT_SUBDIRS = [
    SOURCE_DIR_NAME,
    INTERMEDIATE_DIR_NAME,
    CLIPS_DIR_NAME,
    OUTPUT_DIR_NAME,
]