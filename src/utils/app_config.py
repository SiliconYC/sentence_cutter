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
# 将所有资源路径定义为简单的、从项目根目录算起的相对路径字符串。
# 具体的绝对路径转换工作，交由 get_resource_path 函数在运行时动态完成。
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