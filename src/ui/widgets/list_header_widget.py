# path: src/ui/widgets/list_header_widget.py

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import Qt

class ListHeaderWidget(QWidget):
    """
    一个不可滚动的表头控件，用于显示句子列表的列名。
    其布局与 SentenceCard 保持一致，以实现对齐效果。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(30)
        self.setObjectName("ListHeader")
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 0, 10, 0)
        main_layout.setSpacing(10)

        # 1. 序号列
        index_header = QLabel("序号")
        index_header.setFixedWidth(60)
        index_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 2. 开始时间列
        start_header = QLabel("开始时间")
        start_header.setFixedWidth(100)
        start_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 3. 结束时间列
        end_header = QLabel("结束时间")
        end_header.setFixedWidth(100)
        end_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 4. 正文列 (自动伸展)
        text_header = QLabel("正文内容")
        
        main_layout.addWidget(index_header)
        main_layout.addWidget(start_header)
        main_layout.addWidget(end_header)
        main_layout.addWidget(text_header, 1)

        self.setStyleSheet("""
            QWidget#ListHeader {
                background-color: #3c424a;
                border-bottom: 2px solid #2c3136;
            }
            QLabel {
                font-size: 13px;
                font-weight: bold;
                color: #b0bec5;
            }
        """)