# path: src/ui/sorting_view.py

# 排序视图模块 (三步式流程的第三步)

from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt

class SortingView(QWidget):
    """
    排序界面的占位符。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        label = QLabel("第三步：排序视图 (开发中)")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)