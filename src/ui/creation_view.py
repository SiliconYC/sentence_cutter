# path: src/ui/creation_view.py

# 创建视图模块 (三步式流程的第一步)

from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Signal
from .widgets.vertical_button_panel import VerticalButtonPanel
from .widgets.message_dialogs import MessageBoxes

class CreationView(QWidget):
    """
    负责项目初始化的UI界面。
    提供“打开素材目录”和“开始初始化”两个按钮。
    """
    initialization_successful = Signal()

    def __init__(self, controller, project_path, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.project_path = project_path

        layout = QVBoxLayout(self)
        layout.setContentsMargins(50, 50, 50, 50)

        # 按钮配置
        button_configs = [
            {
                "text": "打开素材目录",
                "obj_name": "open_source_btn",
                "slot": self.controller.open_source_directory,
                "tooltip": "打开 '01_Source' 文件夹，请将SRT字幕文件放入其中。"
            },
            {
                "text": "开始初始化",
                "obj_name": "init_btn",
                "slot": self._on_initialize,
                "tooltip": "解析SRT字幕文件，准备进入下一步。"
            }
        ]

        prompt_text = f"项目已加载\n请将SRT文件放入源目录后开始初始化"
        self.button_panel = VerticalButtonPanel(self, prompt_text, button_configs)
        layout.addWidget(self.button_panel)

    def _on_initialize(self):
        """点击“初始化”按钮的槽函数。"""
        is_success, message = self.controller.initialize_project_media()
        
        if is_success:
            MessageBoxes.show_message(self, "成功", message, "success")
            self.initialization_successful.emit()
        else:
            MessageBoxes.show_message(self, "初始化失败", message, "warning")