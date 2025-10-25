# path: src/ui/views/welcome_view.py

# ◔ 说明: 从通用组件库 A1_新建与载入项目的按钮面板.py 移植而来。
#          作为应用启动或项目重置后的初始欢迎界面。

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt, Signal

class WelcomeView(QWidget):
    """
    应用启动时显示的初始面板，提供新建项目和载入项目的功能按钮。
    """
    new_project_requested = Signal()
    load_project_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        """初始化UI布局和控件。"""
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("""
            QWidget {
                background-color: #2c3e50;
                border: none;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 欢迎文本 - 通过setObjectName来应用全局样式
        welcome_text = "欢迎使用 句子粗剪器\n请开始一个新项目或加载现有项目"
        label = QLabel(welcome_text)
        label.setObjectName("welcomeLabel") # 关键：设置对象名
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(label)
        main_layout.addSpacing(60)

        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)
        
        self.new_button = self._create_button("新建项目", ("#16a085", "#1abc9c"))
        self.load_button = self._create_button("载入项目", ("#2980b9", "#3498db"))
        
        self.new_button.clicked.connect(self.new_project_requested)
        self.load_button.clicked.connect(self.load_project_requested)

        button_layout.addWidget(self.new_button)
        button_layout.addWidget(self.load_button)
        main_layout.addLayout(button_layout)

    def _create_button(self, text, colors):
        """创建一个样式化的按钮。"""
        normal_color, hover_color = colors
        button = QPushButton(text)
        button.setObjectName("welcomeButton") # 关键：设置对象名

        # 关键：手动设置鼠标悬停光标为手形
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        
        button.setFixedSize(300, 100)
        # 按钮的具体颜色样式仍然在这里设置，因为它们是实例相关的，
        # 而字体等通用样式由全局QSS控制。
        button.setStyleSheet(f"""
            QPushButton#welcomeButton {{
                background-color: {normal_color};
                border: none;
                border-radius: 12px;
                color: white;
            }}
            QPushButton#welcomeButton:hover {{
                background-color: {hover_color};
            }}
        """)
        return button