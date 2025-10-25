# path: src/ui/widgets/icon_toolbar/toolbar_factory.py

# ◔ 说明: 从通用组件库迁移而来，原名为“tooli_创建器”。
#          这是一个工厂类，用于根据配置动态创建水平或垂直的图标工具栏。

import os
import sys
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QHBoxLayout, QVBoxLayout, QWidget, QFrame, QScrollArea, QSizePolicy
)

from .icon_button import IconButton
from utils.resource_path import get_resource_path

class _ContentFittingScrollArea(QScrollArea):
    """一个私有辅助类, 通过重写sizeHint来修复QScrollArea不报告其内容真实高度的问题。"""
    def sizeHint(self) -> QSize:
        if self.widget():
            return self.widget().sizeHint()
        return super().sizeHint()

class IconToolbarFactory:
    """
    根据配置创建并返回一个可滚动的图标式工具栏实例。
    """
    DEFAULT_ICON_DIR = "assets/icons/toolbar"

    def __init__(self, configs, icon_size=60, orientation="horizontal", bg_color=None):
        self.configs = configs
        self.icon_size = icon_size
        self.orientation = orientation
        self.bg_color = bg_color
        self.buttons = {}

    def create(self):
        """创建并返回工具栏实例。"""
        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: transparent;")

        layout = QHBoxLayout() if self.orientation == "horizontal" else QVBoxLayout()
        align = Qt.AlignmentFlag.AlignLeft if self.orientation == "horizontal" else Qt.AlignmentFlag.AlignTop
        layout.setAlignment(align)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        content_widget.setLayout(layout)

        self._populate_content(layout)
        
        scroll_area = _ContentFittingScrollArea() if self.orientation == "vertical" else QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        if self.orientation == "horizontal":
            scroll_area.setFixedHeight(self.icon_size + 20)
            scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        else: # vertical
            scroll_area.setWidgetResizable(False)
            scroll_area.setFixedWidth(self.icon_size + 12)
            scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            scroll_area.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
            
        scroll_area.setObjectName("iconToolbarScrollArea")
        scroll_area.setWidget(content_widget)
        scroll_area.viewport().setStyleSheet("background-color: transparent;")
        self._apply_scroll_area_style(scroll_area)
        
        return scroll_area

    def _apply_scroll_area_style(self, scroll_area):
        style = "QScrollArea#iconToolbarScrollArea { border: none; background-color: transparent; }"
        if self.bg_color:
            r, g, b, a = self.bg_color
            style = f"QScrollArea#iconToolbarScrollArea {{ border: none; background-color: rgba({r}, {g}, {b}, {a}); border-radius: 8px; }}"
        scroll_area.setStyleSheet(style)

    def _populate_content(self, layout):
        for config in self.configs:
            if not config:
                layout.addWidget(self._create_separator())
                continue
            
            text, icon_filename, slot = config
            
            # 【核心修改】将路径解析和占位符逻辑完全封装在此处
            absolute_icon_path = ""
            try:
                relative_path = os.path.join(self.DEFAULT_ICON_DIR, icon_filename).replace('\\', '/')
                absolute_icon_path = get_resource_path(relative_path)
            except FileNotFoundError:
                print(f"警告: 找不到工具栏图标 '{relative_path}', 将使用占位符。")
                try:
                    # 如果找不到图标，则尝试加载占位符图标
                    absolute_icon_path = get_resource_path(IconButton.PLACEHOLDER_ICON)
                except FileNotFoundError:
                    # 如果连占位符都找不到，则路径为空，按钮将不显示图片
                    print(f"严重警告: 连占位符图标都找不到: '{IconButton.PLACEHOLDER_ICON}'")

            button = IconButton(text, absolute_icon_path, self.icon_size, self.orientation)
            if callable(slot):
                button.clicked.connect(slot)
            
            self.buttons[text] = button
            layout.addWidget(button)

    def _create_separator(self):
        separator = QFrame()
        shape = QFrame.Shape.VLine if self.orientation == "horizontal" else QFrame.Shape.HLine
        separator.setFrameShape(shape)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("color: grey;")
        return separator