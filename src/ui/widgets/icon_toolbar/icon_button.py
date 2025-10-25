# path: src/ui/widgets/icon_toolbar/icon_button.py

# ◔ 说明: 从通用组件库迁移而来，原名为“工具栏按钮”。
#          这是构成图标工具栏的基本单元。

import os
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap, QColor
from PySide6.QtWidgets import QPushButton, QVBoxLayout, QLabel

class IconButton(QPushButton):
    """
    一个专门用于图标工具栏的按钮，支持图标和文本，以及两种显示模式（水平/垂直）。
    它只负责显示，不负责解析或验证路径。
    """
    # 【核心修改 1】占位符图标路径也改为标准的相对路径
    PLACEHOLDER_ICON = "assets/icons/toolbar/placeholder.png"

    def __init__(self, text, icon_path, icon_size, mode="horizontal"):
        super().__init__()
        self.button_text = text
        # 【核心修改 2】直接使用传入的路径，不再进行验证
        self.icon_path = icon_path
        self.icon_size = icon_size
        self.mode = mode
        
        self._setup_styles()
        self._init_ui()

    # 【核心修改 3】移除 _validate_icon_path 方法，路径验证逻辑上移到 Factory 中

    def _setup_styles(self):
        self.text_color_normal = QColor("#b2bec3")
        self.text_color_hover = QColor("#d35400")
        self.text_color_pressed = QColor("#c0392b")
        self.bg_color_hover = "rgba(100, 100, 100, 50)"
        self.bg_color_pressed = "rgba(100, 100, 100, 80)"

    def _init_ui(self):
        self.setFlat(True)
        self.setCursor(Qt.CursorShape.ArrowCursor)

        if self.mode == "horizontal":
            self._init_horizontal_layout()
        else:
            self._init_vertical_layout()
        
        self._update_style("normal")

    def _init_horizontal_layout(self):
        margin = 5 if self.icon_size >= 80 else 2
        self.setFixedSize(QSize(self.icon_size, self.icon_size))
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(margin, margin, margin, margin)
        
        self.icon_label = self._create_icon_label(0.6)
        layout.addWidget(self.icon_label)

        self.text_label = QLabel(self.button_text, self)
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.text_label)
    
    def _init_vertical_layout(self):
        self.setFixedSize(QSize(self.icon_size, self.icon_size))
        self.setToolTip(self.button_text)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.icon_label = self._create_icon_label(0.7)
        layout.addWidget(self.icon_label)
        
        self.text_label = QLabel(self)
        self.text_label.setVisible(False)

    def _create_icon_label(self, scale_ratio):
        label = QLabel(self)
        # self.icon_path 此处应该已经是绝对路径
        pixmap = QPixmap(self.icon_path)
        if pixmap.isNull():
            # 只有在绝对路径加载失败时才打印警告
            if self.icon_path:
                print(f"[警告] 无法加载图标: {self.icon_path}")
        else:
            size = int(self.icon_size * scale_ratio)
            scaled_pixmap = pixmap.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            label.setPixmap(scaled_pixmap)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return label

    def _update_style(self, state="normal"):
        if self.mode == "horizontal":
            color = self.text_color_normal.name()
            if state == "hover": color = self.text_color_hover.name()
            elif state == "pressed": color = self.text_color_pressed.name()
            self.text_label.setStyleSheet(f"color: {color};")
        else: # vertical mode
            style = "QPushButton { border: none; background-color: transparent; border-radius: 4px; }"
            if state == "hover": style += f"QPushButton:hover {{ background-color: {self.bg_color_hover}; }}"
            elif state == "pressed": style += f"QPushButton:pressed {{ background-color: {self.bg_color_pressed}; }}"
            self.setStyleSheet(style)

    def enterEvent(self, event):
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._update_style("hover")
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self._update_style("normal")
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        self._update_style("pressed")
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        state = "hover" if self.rect().contains(event.pos()) else "normal"
        self._update_style(state)
        super().mouseReleaseEvent(event)