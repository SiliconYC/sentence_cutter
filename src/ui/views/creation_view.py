# path: src/ui/views/creation_view.py

# 创建视图模块 (三步式流程的第一步)

from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Signal
from ui.widgets.vertical_button_panel import VerticalButtonPanel
from ui.widgets.message_dialogs import MessageBoxes

class CreationView(QWidget):
    """
    负责项目初始化的UI界面。
    提供“打开素材目录”和“开始初始化”两个按钮。
    """
    ready_for_next = Signal(bool)
    initialization_completed = Signal() # 职责清晰的信号：初始化已完成

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
        self.button_panel.reinitialization_requested.connect(self._on_initialize)
        layout.addWidget(self.button_panel)

    def _on_initialize(self):
        """
        点击“初始化”按钮或链接的槽函数。
        如果检测到后续步骤已有操作, 会弹出警告。
        成功后会发出完成信号。
        """
        if self.controller.model.is_initialized and (sum(self.controller.model.selection_state) > 0 or len(self.controller.model.final_sequence) > 0):
            confirmed = MessageBoxes.ask_confirmation(
                self, "确认重新初始化",
                "检测到您已有编辑记录。\n重新初始化将会清空所有筛选和排序结果。\n\n您确定要继续吗？"
            )
            if not confirmed:
                return

        is_success, message = self.controller.initialize_project_media()
        
        if is_success:
            MessageBoxes.show_message(self, "成功", message, "success")
            self.ready_for_next.emit(True)
            self.initialization_completed.emit() # 发出完成信号
        else:
            MessageBoxes.show_message(self, "初始化失败", message, "warning")
            self.ready_for_next.emit(False)

    def enter_view(self):
        """当该视图被显示时调用。"""
        # 检查是否存在编辑记录，并更新初始化按钮的显示状态
        has_edits = sum(self.controller.model.selection_state) > 0 or len(self.controller.model.final_sequence) > 0
        self.button_panel.update_initialization_button_state(has_edits)
        
        is_ready = self.controller.model.is_initialized
        self.ready_for_next.emit(is_ready)
    
    def reset_view_state(self):
        """重置视图状态的API。创建页无需具体操作。"""
        pass # 符合API协定, 但此视图没有需要重置的状态