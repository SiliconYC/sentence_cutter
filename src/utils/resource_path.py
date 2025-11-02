# path: src/utils/resource_path.py

import sys
from pathlib import Path

def get_resource_path(relative_path: str) -> str:
    """
    获取资源文件的绝对路径，智能适配开发环境和PyInstaller打包环境。

    在开发环境中，它会从项目根目录（即.py文件的上三级目录）开始计算。
    在PyInstaller打包后的环境中，它会从临时解压目录（sys._MEIPASS）开始计算。

    Args:
        relative_path (str): 从项目根目录算起的相对路径字符串。
                           例如: "assets/icons/paper-cut.png"

    Returns:
        str: 资源的绝对路径。

    Raises:
        FileNotFoundError: 如果在最终计算出的路径下找不到该文件。
    """
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        base_path = Path(sys._MEIPASS)
    else:
        # src/utils/resource_path.py -> src/utils -> src -> root
        base_path = Path(__file__).resolve().parent.parent.parent

    final_path = base_path / relative_path

    if not final_path.exists():
        raise FileNotFoundError(f"无法找到资源: '{final_path}'")

    return str(final_path)