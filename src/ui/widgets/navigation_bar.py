# path: src/ui/widgets/navigation_bar.py

from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PySide6.QtCore import Signal

class NavigationBar(QWidget):
    """
    一个可复用的底部导航栏控件。
    包含“上一步”和“下一步”按钮，并提供信号和方法来控制其行为。
    """
    previous_clicked = Signal()
    next_clicked = Signal()
    help_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("NavigationBar")
        self.setFixedHeight(50)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 5, 10, 5)

        # 左侧标准按钮
        self.prev_button = QPushButton("上一步")
        self.prev_button.setMinimumWidth(100)
        self.prev_button.clicked.connect(self.previous_clicked)
        
        self.help_button = QPushButton("当前页说明")
        self.help_button.setMinimumWidth(120)
        self.help_button.clicked.connect(self.help_clicked)

        self.next_button = QPushButton("下一步")
        self.next_button.setMinimumWidth(100)
        self.next_button.clicked.connect(self.next_clicked)

        main_layout.addWidget(self.prev_button)
        main_layout.addWidget(self.help_button)
        main_layout.addWidget(self.next_button)
        main_layout.addStretch(1)

        # 右侧自定义按钮区域
        self.custom_widget_layout = QHBoxLayout()
        main_layout.addLayout(self.custom_widget_layout)

        self.setStyleSheet("""
            QWidget#NavigationBar {
                background-color: #2c3136;
                border-top: 1px solid #444;
            }
            QPushButton {
                min-height: 30px;
                font-size: 14px;
            }
        """)

    def add_custom_widget(self, widget: QWidget):
        """向导航栏右侧添加自定义控件。"""
        self.custom_widget_layout.addWidget(widget)

    def set_previous_enabled(self, enabled: bool):
        self.prev_button.setEnabled(enabled)

    def set_next_enabled(self, enabled: bool):
        self.next_button.setEnabled(enabled)