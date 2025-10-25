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
                                 "vendor/ffmpeg_win/ffmpeg.exe"
                                 "README.md"

    Returns:
        str: 资源的绝对路径。

    Raises:
        FileNotFoundError: 如果在最终计算出的路径下找不到该文件。
    """
    # 判断是否在PyInstaller打包的环境中
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # 打包环境: 根目录是 sys._MEIPASS (一个临时解压目录)
        base_path = Path(sys._MEIPASS)
    else:
        # 开发环境: 根目录是此文件 (resource_path.py) 的上三级目录
        # (src/utils/resource_path.py -> src/utils -> src -> root)
        base_path = Path(__file__).resolve().parent.parent.parent

    # 将计算出的根路径与传入的相对路径拼接成最终路径
    final_path = base_path / relative_path

    # 为确保健壮性，检查文件是否存在
    if not final_path.exists():
        raise FileNotFoundError(f"无法找到资源: '{final_path}'")

    return str(final_path)

# --- 简单测试代码 ---
# 在开发环境中运行时，可以快速验证此脚本的路径计算逻辑是否正确。
if __name__ == '__main__':
    print("--- 资源路径解析器测试 (开发环境) ---")
    try:
        # 尝试定位一个已知存在的文件
        readme_path = get_resource_path('README.md')
        print(f"[OK] 成功定位 README.md: {readme_path}")
        assert Path(readme_path).is_file()

        # 尝试定位一个已知存在的目录中的文件
        icon_path = get_resource_path('assets/icons/paper-cut.png')
        print(f"[OK] 成功定位 paper-cut.png: {icon_path}")
        assert Path(icon_path).is_file()
        
        # 尝试定位一个不存在的文件，预期会引发 FileNotFoundError
        print("\n正在测试一个不存在的文件 (预期会报错)...")
        get_resource_path('non_existent_file.txt')

    except FileNotFoundError as e:
        print(f"[OK] 成功捕获到预期的错误: {e}")
    except Exception as e:
        print(f"[失败] 发生了意外的错误: {e}")