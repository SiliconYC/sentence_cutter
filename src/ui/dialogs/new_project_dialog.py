# path: src/ui/dialogs/new_project_dialog.py

# ◔ 说明: 从通用组件库 B1_新建项目的窗口.py 移植并现代化改造。
#          增加了“项目根目录”选择功能，逻辑更清晰。

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, 
    QPushButton, QDialogButtonBox, QFileDialog, QFormLayout
)
from PySide6.QtCore import Qt
import os
import datetime

class NewProjectDialog(QDialog):
    """
    一个对话框，用于收集创建新项目所需的信息：
    1. 项目根目录 (所有项目的存放位置)
    2. 新项目的名称
    """
    def __init__(self, parent=None, last_root_dir=""):
        super().__init__(parent)
        self.setWindowTitle("创建新项目")
        self.setMinimumWidth(400)
        
        self.last_root_dir = last_root_dir
        self.project_info = {}

        # 布局和控件
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # 1. 项目根目录选择
        self.root_dir_edit = QLineEdit(last_root_dir)
        self.root_dir_button = QPushButton("浏览...")
        self.root_dir_button.clicked.connect(self._select_root_dir)
        
        root_dir_layout = QHBoxLayout()
        root_dir_layout.addWidget(self.root_dir_edit)
        root_dir_layout.addWidget(self.root_dir_button)
        form_layout.addRow("项目根目录:", root_dir_layout)

        # 2. 项目名称输入
        today = datetime.date.today().strftime("%Y%m%d")
        self.project_name_edit = QLineEdit(f"{today}_新项目")
        form_layout.addRow("新项目名称:", self.project_name_edit)
        
        layout.addLayout(form_layout)
        
        # 确认/取消按钮
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _select_root_dir(self):
        directory = QFileDialog.getExistingDirectory(
            self,
            "请选择存放所有项目的根目录",
            self.root_dir_edit.text() or os.path.expanduser("~")
        )
        if directory:
            self.root_dir_edit.setText(directory)

    def accept(self):
        """当用户点击OK时，验证并保存信息。"""
        root_dir = self.root_dir_edit.text().strip()
        project_name = self.project_name_edit.text().strip()

        if not root_dir or not os.path.isdir(root_dir):
            print("[错误] 请提供一个有效的项目根目录。")
            return

        if not project_name or any(c in r'/\:*?"<>|' for c in project_name):
            print("[错误] 项目名称不能为空且不能包含非法字符。")
            return
            
        self.project_info = {
            "root_dir": root_dir,
            "project_name": project_name
        }
        super().accept()

    def get_project_info(self):
        return self.project_info