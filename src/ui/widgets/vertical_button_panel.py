# path: src/ui/widgets/vertical_button_panel.py

# ◔ 说明: 从通用组件库迁移而来。一个通用的纵列按钮面板，通过配置列表生成按钮并绑定槽函数。
#          非常适合用于“创建”这种步骤简单、选项明确的界面。

import sys
from PySide6.QtWidgets import (
    QVBoxLayout, QLabel, QPushButton,
    QWidget, QSizePolicy, QApplication, QMainWindow
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt, Signal

class VerticalButtonPanel(QWidget):
    """
    一个通用的纵列按钮面板，支持通过按钮配置列表生成按钮并绑定槽函数。
    提供状态提示标签和一组垂直排列的操作按钮。
    """
    reinitialization_requested = Signal()

    def __init__(self, parent, prompt_text, button_configs):
        """
        Args:
            parent: 父控件对象。
            prompt_text (str): 面板顶部显示的提示文字。
            button_configs (list): 按钮配置列表，格式为:
                [{"text": str, "obj_name": str, "slot": callable, "tooltip": str (可选)}, ...]
        """
        super().__init__(parent)
        self.prompt_text = prompt_text
        self.button_configs = button_configs
        self.button_spacing = 15
        self.init_button = None
        self.warning_label = None

        # 预设的扁平化UI颜色对 (常规色, 悬停色)
        self.color_pairs = [
            ("#27ae60", "#2ecc71"),  # Green
            ("#2980b9", "#3498db"),  # Blue
            ("#d35400", "#e67e22"),  # Orange
            ("#c0392b", "#e74c3c"),  # Red
            ("#8e44ad", "#9b59b6"),  # Purple
            ("#2c3e50", "#34495e"),  # Gray
        ]

        self._validate_configs()
        self._init_ui()

    def _validate_configs(self):
        """验证传入的按钮配置是否合法。"""
        if len(self.button_configs) > len(self.color_pairs):
            raise ValueError(f"按钮数量不能超过 {len(self.color_pairs)} 个")
        for config in self.button_configs:
            if not all(key in config for key in ["text", "obj_name", "slot"]):
                raise ValueError("按钮配置必须包含 'text', 'obj_name', 和 'slot' 键。")

    def _init_ui(self):
        """初始化整体UI布局和样式。"""
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 0.1);
                border-radius: 8px;
            }
            QLabel {
                background: transparent;
                border: none;
            }
        """)

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.setContentsMargins(30, 30, 30, 30)

        # 提示标签
        prompt_label = QLabel(self.prompt_text)
        prompt_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        prompt_label.setFont(QFont("Arial", 24))
        prompt_label.setStyleSheet("color: #cccccc;")
        main_layout.addWidget(prompt_label)
        main_layout.addSpacing(40)

        # 按钮布局
        button_layout = QVBoxLayout()
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        button_layout.setSpacing(self.button_spacing)

        for i, config in enumerate(self.button_configs):
            normal_color, hover_color = self.color_pairs[i]
            button = QPushButton(config["text"])
            button.setObjectName(config["obj_name"])
            button.setFont(QFont("Arial", 20, QFont.Weight.Bold))
            button.setFixedSize(320, 80)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {normal_color};
                    border: none;
                    border-radius: 8px;
                    color: white;
                    padding: 15px 32px;
                }}
                QPushButton:hover {{
                    background-color: {hover_color};
                }}
                QPushButton:disabled {{
                    background-color: #555555;
                    color: #999999;
                }}
            """)
            
            if "tooltip" in config:
                button.setToolTip(config["tooltip"])

            button.clicked.connect(config["slot"])
            setattr(self, config["obj_name"], button)
            button_layout.addWidget(button)

            # 存储初始化按钮的引用
            if config["obj_name"] == "init_btn":
                self.init_button = button

        # 创建并添加警告标签
        self.warning_label = QLabel()
        self.warning_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.warning_label.setTextFormat(Qt.TextFormat.RichText)
        self.warning_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        self.warning_label.setOpenExternalLinks(False)
        # 【样式修复】为 <a> 标签添加 text-decoration: none !important; 来强制移除虚线
        self.warning_label.setText(
            '<div style="color: #9e9e9e; font-size: 13px;">'
            '点击<a href="reinitialize" style="color: #e67e22; text-decoration: none !important;">此处可重新初始化</a>，请谨慎操作。<br>'
            '这会清除所有的后续编辑成果, 且永远无法恢复。'
            '</div>'
        )
        self.warning_label.linkActivated.connect(self._on_reinitialize_link_activated)
        self.warning_label.setVisible(False) # 默认隐藏
        button_layout.addWidget(self.warning_label)


        main_layout.addLayout(button_layout)

    def _on_reinitialize_link_activated(self, link: str):
        """当“重新初始化”超链接被点击时触发。"""
        if link == "reinitialize":
            self.reinitialization_requested.emit()

    def update_initialization_button_state(self, has_edits: bool):
        """根据是否存在编辑记录，更新初始化按钮的显示状态。"""
        if not self.init_button:
            return
            
        if has_edits:
            self.init_button.setVisible(False)
            self.warning_label.setVisible(True)
        else:
            self.init_button.setVisible(True)
            self.warning_label.setVisible(False)