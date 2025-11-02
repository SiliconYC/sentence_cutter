# path: src/ui/widgets/waiting_spinner_dialog.py

# ◔ 说明: 从通用组件库迁移而来。一个在执行耗时操作时显示的模态“菊花图”弹窗。

import sys
import os
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QApplication, QPushButton, QWidget
from PySide6.QtGui import QMovie
from PySide6.QtCore import Qt, QSize, QTimer

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
        
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.CustomizeWindowHint)
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)

        try:
            self.spinner_gif_path = get_resource_path("assets/icons/loading_spinner.gif")
        except FileNotFoundError as e:
            print(f"[严重错误] {e}")
            self.spinner_gif_path = ""

        self._init_ui(text)
        self.setFixedSize(280, 180)
        self.setStyleSheet("background-color: #333; color: #eee;")

    def _init_ui(self, text):
        """初始化弹窗的内部布局和控件。"""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)

        self.animation_label = QLabel(self)
        self.movie = QMovie(self.spinner_gif_path)
        self.movie.setScaledSize(QSize(96, 96))
        self.animation_label.setMovie(self.movie)
        layout.addWidget(self.animation_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
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