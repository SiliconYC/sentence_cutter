# path: src/ui/widgets/waiting_spinner_dialog.py

# ◔ 说明: 从通用组件库迁移而来。一个在执行耗时操作时显示的模态“菊花图”弹窗。

import sys
import os
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QApplication, QPushButton, QWidget
from PySide6.QtGui import QMovie
from PySide6.QtCore import Qt, QSize, QTimer

# 【核心修改 1】 导入工具
from utils.resource_path import get_resource_path

class WaitingSpinnerDialog(QDialog):
    """
    一个不可关闭的模态弹窗，用于在执行耗时操作时显示等待动画。
    """
    def __init__(
            self,
            parent=None,
            title="请稍候...",
            text="正在处理中，请稍候...",
            is_modal=True
        ):
        super().__init__(parent)

        self.setWindowTitle(title)
        self.setModal(is_modal)
        
        # 禁用关闭按钮
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.CustomizeWindowHint)
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)

        # 【核心修改 2】 使用 get_resource_path 获取 GIF 的绝对路径
        try:
            self.spinner_gif_path = get_resource_path("assets/icons/loading_spinner.gif")
        except FileNotFoundError as e:
            print(f"严重错误: {e}")
            self.spinner_gif_path = ""

        self._init_ui(text)
        self.setFixedSize(280, 180)
        self.setStyleSheet("background-color: #333; color: #eee;")

    def _init_ui(self, text):
        """初始化弹窗的内部布局和控件。"""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)

        # 添加动画
        self.animation_label = QLabel(self)
        self.movie = QMovie(self.spinner_gif_path)
        self.movie.setScaledSize(QSize(96, 96))
        self.animation_label.setMovie(self.movie)
        layout.addWidget(self.animation_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # 添加提示文本
        prompt_label = QLabel(text, self)
        prompt_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        prompt_label.setWordWrap(True)
        layout.addWidget(prompt_label, alignment=Qt.AlignmentFlag.AlignCenter)

    def showEvent(self, event):
        """窗口显示时自动开始播放动画。"""
        if not self.spinner_gif_path or not os.path.exists(self.spinner_gif_path):
            print(f"[错误] 动画文件不存在或路径无效")
            self.animation_label.setText("[动画加载失败]")
        else:
            self.movie.start()
        super().showEvent(event)

    def closeEvent(self, event):
        """窗口关闭时安全地停止动画。"""
        self.movie.stop()
        super().closeEvent(event)

# ------------------- 测试代码 -------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = QWidget()
    main_window.setWindowTitle("WaitingSpinnerDialog Test")
    main_window.setGeometry(100, 100, 300, 100)
    
    button = QPushButton("点击测试等待弹窗 (模拟3秒操作)", main_window)
    
    def test_dialog():
        print("[测试] 准备打开等待弹窗...")
        dialog = WaitingSpinnerDialog(main_window)
        # 模拟一个3秒的耗时操作，完成后关闭对话框
        QTimer.singleShot(3000, lambda: dialog.accept())
        dialog.exec()
        print("[测试] 模拟操作完成，弹窗已关闭。")

    button.clicked.connect(test_dialog)
    button.move(50, 40)
    main_window.show()
    sys.exit(app.exec())