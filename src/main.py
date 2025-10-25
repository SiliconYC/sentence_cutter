# path: src/main.py

# 应用程序主入口
#
# 功能职责:
# 1. 作为整个程序的启动点。
# 2. 初始化 Qt 应用程序实例 (QApplication)。
# 3. 实例化我们自定义的样式管理器，并应用全局样式。
# 4. 实例化主窗口 (MainWindow)。。
# 5. 显示主窗口。
# 6. 启动应用程序的事件循环 (app.exec())，并处理退出。

import sys
from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow
from utils.custom_style_manager import CustomStyleManager

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 在创建任何窗口之前，先应用全局自定义样式
    style_manager = CustomStyleManager(app)
    style_manager.apply_style()
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())