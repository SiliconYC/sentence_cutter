# path: src/ui/main_window.py

# 主窗口模块

import os
from PySide6.QtWidgets import QMainWindow, QStackedWidget
from PySide6.QtGui import QIcon, QAction, QKeySequence, QCloseEvent

from app_logic import ProjectController, ProjectModel, EditorController
from ui.views.welcome_view import WelcomeView
from ui.views.editor_view import EditorView
from ui.widgets.markdown_viewer import MarkdownViewer
from utils.app_config import APP_NAME, ICON_PATH
from utils.resource_path import get_resource_path

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        
        try:
            absolute_icon_path = get_resource_path(ICON_PATH)
            self.setWindowIcon(QIcon(absolute_icon_path))
        except FileNotFoundError:
            print(f"[警告] 无法找到应用程序图标: {ICON_PATH}")

        self.setGeometry(100, 100, 1280, 720)

        # MVC核心组件
        self.model = ProjectModel()
        self.project_controller = ProjectController(self, self.model)
        self.editor_controller = EditorController(self.model, self)

        self._init_ui()
        self._create_actions()
        self._create_menus()
        
        self.show_welcome_view()

    def _init_ui(self):
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        self.welcome_view = WelcomeView(self)
        self.stacked_widget.addWidget(self.welcome_view)

        self.welcome_view.new_project_requested.connect(self.project_controller.new_project)
        self.welcome_view.load_project_requested.connect(self.project_controller.load_project)

    def _create_actions(self):
        self.new_action = QAction("新建", self)
        self.new_action.triggered.connect(self.project_controller.new_project)
        self.load_action = QAction("载入", self)
        self.load_action.triggered.connect(self.project_controller.load_project)
        self.save_action = QAction("保存", self)
        self.save_action.setShortcut(QKeySequence.StandardKey.Save)
        self.save_action.triggered.connect(lambda: self.project_controller.save_project(show_notification=True))
        self.reset_action = QAction("重置", self)
        self.reset_action.triggered.connect(self.project_controller.reset_project)
        self.about_action = QAction(f"关于{APP_NAME}", self)
        self.about_action.triggered.connect(self._show_about_dialog)

    def _create_menus(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("文件")
        file_menu.addAction(self.new_action)
        file_menu.addAction(self.load_action)
        file_menu.addAction(self.save_action)
        file_menu.addSeparator()
        file_menu.addAction(self.reset_action)
        help_menu = menu_bar.addMenu("帮助")
        help_menu.addAction(self.about_action)

    def _show_about_dialog(self):
        dialog = MarkdownViewer(self, f"关于 {APP_NAME}", markdown_path="README.md")
        dialog.exec()

    def closeEvent(self, event: QCloseEvent):
        """重写关闭事件，以实现自动保存。"""
        print("\n\n[信息] 主窗口关闭事件触发，正在静默保存项目...")
        self.project_controller.save_project(show_notification=False)
        event.accept()

    # --- 公共接口 ---
    def show_welcome_view(self):
        self.stacked_widget.setCurrentWidget(self.welcome_view)
        self.setWindowTitle(APP_NAME)
        self.save_action.setEnabled(False)
        self.reset_action.setEnabled(False)

    def show_editor_view(self):
        old_editor = self.findChild(EditorView)
        if old_editor:
            self.stacked_widget.removeWidget(old_editor)
            old_editor.deleteLater()
            
        editor_view = EditorView(self.editor_controller, self.model.project_path, parent=self)
        self.stacked_widget.addWidget(editor_view)
        self.stacked_widget.setCurrentWidget(editor_view)
        self.setWindowTitle(f"{APP_NAME} - {os.path.basename(self.model.project_path)}")
        self.save_action.setEnabled(True)
        self.reset_action.setEnabled(True)