# path: src/ui/views/editor_view.py

import os
import time
from PySide6.QtWidgets import QWidget, QStackedWidget, QVBoxLayout, QPushButton, QFileDialog
from PySide6.QtCore import QThread, QUrl
from PySide6.QtGui import QDesktopServices
from .creation_view import CreationView
from .selection_view import SelectionView
from .sorting_view import SortingView
from ui.widgets.navigation_bar import NavigationBar
from ui.widgets.markdown_viewer import MarkdownViewer
from ui.widgets.message_dialogs import MessageBoxes
from ui.widgets.waiting_spinner_dialog import WaitingSpinnerDialog
from app_logic.editor_controller import SynthesisWorker
from ui.widgets.icon_toolbar.toolbar_factory import IconToolbarFactory

class EditorView(QWidget):
    def __init__(self, controller, project_path, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.project_path = project_path
        self.model = self.controller.model 
        self.help_files = ["assets/help/creation_view_help.md", "assets/help/selection_view_help.md", "assets/help/sorting_view_help.md"]
        self.help_titles = ["“创建”页使用说明", "“筛选”页使用说明", "“排序”页使用说明"]

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.toolbar = self._create_toolbar()
        main_layout.addWidget(self.toolbar)

        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget, 1)

        self.creation_view = CreationView(self.controller, self.project_path)
        self.selection_view = SelectionView(self.controller, self.model)
        self.sorting_view = SortingView(self.controller, self.model)

        self.stacked_widget.addWidget(self.creation_view)
        self.stacked_widget.addWidget(self.selection_view)
        self.stacked_widget.addWidget(self.sorting_view)

        self.nav_bar = NavigationBar(self)
        self._setup_custom_buttons()
        main_layout.addWidget(self.nav_bar)

        self._connect_signals()
        self._update_navigation_state(0)

    def _create_toolbar(self):
        """创建并配置顶部图标工具栏。"""
        project_controller = self.parent().project_controller
        
        toolbar_configs = [
            ("新建项目", "email_plus.png", project_controller.new_project),
            ("载入项目", "email_picture.png", project_controller.load_project),
            ("保存项目", "save_file.png", lambda: project_controller.save_project(show_notification=True)),
            (),
            ("撤销", "traffic_left_bend.png", self._on_undo_clicked),
            ("重做", "traffic_right_bend.png", self._on_redo_clicked)
        ]
        
        factory = IconToolbarFactory(toolbar_configs, icon_size=60, orientation="horizontal")
        toolbar_widget = factory.create()

        self.undo_button = factory.buttons.get("撤销")
        self.redo_button = factory.buttons.get("重做")

        return toolbar_widget

    def _setup_custom_buttons(self):
        """创建并添加特定视图的自定义按钮到导航栏。"""
        self.export_button = QPushButton("合成视频")
        self.export_button.setMinimumWidth(120)
        self.export_button.clicked.connect(self.on_synthesize_video)
        self.nav_bar.add_custom_widget(self.export_button)

    def _connect_signals(self):
        self.nav_bar.previous_clicked.connect(self.go_to_previous_view)
        self.nav_bar.next_clicked.connect(self.go_to_next_view)
        self.nav_bar.help_clicked.connect(self._show_help_dialog)
        self.stacked_widget.currentChanged.connect(self._update_navigation_state)
        self.creation_view.ready_for_next.connect(self.nav_bar.set_next_enabled)
        self.selection_view.ready_for_next.connect(self.nav_bar.set_next_enabled)
        self.creation_view.initialization_completed.connect(self.on_initialization_completed)
        self.controller.signals.history_changed.connect(self._update_history_buttons)
        self.controller.signals.sorting_history_changed.connect(self._update_history_buttons)

    def _on_undo_clicked(self):
        """根据当前页面调用相应的撤销方法。"""
        current_view = self.stacked_widget.currentWidget()
        if current_view == self.selection_view:
            self.controller.undo()
        elif current_view == self.sorting_view:
            self.controller.undo_sorting()

    def _on_redo_clicked(self):
        """根据当前页面调用相应的重做方法。"""
        current_view = self.stacked_widget.currentWidget()
        if current_view == self.selection_view:
            self.controller.redo()
        elif current_view == self.sorting_view:
            self.controller.redo_sorting()

    def _update_history_buttons(self, can_undo, can_redo):
        """更新撤销和重做按钮的启用状态。"""
        if self.undo_button:
            self.undo_button.setEnabled(can_undo)
        if self.redo_button:
            self.redo_button.setEnabled(can_redo)

    def go_to_previous_view(self):
        current_index = self.stacked_widget.currentIndex()
        if current_index > 0: self.stacked_widget.setCurrentIndex(current_index - 1)

    def go_to_next_view(self):
        current_index = self.stacked_widget.currentIndex()
        if current_index < self.stacked_widget.count() - 1: self.stacked_widget.setCurrentIndex(current_index + 1)

    def on_initialization_completed(self):
        self.selection_view.reset_view_state()
        self.sorting_view.reset_view_state()
        self.go_to_next_view()
        
    def _show_help_dialog(self):
        current_index = self.stacked_widget.currentIndex()
        if not (0 <= current_index < len(self.help_files)): return
        help_path = self.help_files[current_index]
        help_title = self.help_titles[current_index]
        dialog = MarkdownViewer(self, help_title, markdown_path=help_path)
        dialog.exec()

    def _update_navigation_state(self, index):
        self.nav_bar.set_previous_enabled(index > 0)
        is_last_page = (index == self.stacked_widget.count() - 1)
        self.nav_bar.set_next_enabled(not is_last_page)
        
        current_view = self.stacked_widget.widget(index)
        is_sorting_view = (current_view == self.sorting_view)
        self.export_button.setVisible(is_sorting_view)

        if hasattr(current_view, 'enter_view'):
            current_view.enter_view()
        
        if current_view == self.creation_view:
            self._update_history_buttons(False, False)
        elif current_view == self.selection_view:
            self.controller.refresh_selection_history_status()
        elif current_view == self.sorting_view:
            self.controller.refresh_sorting_history_status()

        is_creation_view = (current_view == self.creation_view)
        if is_creation_view and self.model.is_initialized:
            self.nav_bar.set_next_enabled(True)
        elif is_last_page:
            self.nav_bar.set_next_enabled(False)

    def on_synthesize_video(self):
        if not self.model.final_sequence:
            MessageBoxes.show_message(self, "无法合成", "最终序列为空，无法合成视频。\n请先从左侧列表中添加句子到右侧。", "warning")
            return
        
        source_dir = os.path.join(self.project_path, "01_Source")
        video_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "请选择一个或多个视频素材文件",
            source_dir,
            "视频文件 (*.mp4)"
        )

        if not video_paths:
            return

        self.synthesis_thread = QThread()
        self.synthesis_worker = self.controller.create_synthesis_worker(video_paths)
        self.synthesis_worker.moveToThread(self.synthesis_thread)
        
        self.synthesis_thread.started.connect(self.synthesis_worker.run)
        self.synthesis_worker.finished.connect(self.on_synthesis_finished)
        
        self.synthesis_worker.finished.connect(self.synthesis_thread.quit)
        self.synthesis_worker.finished.connect(self.synthesis_worker.deleteLater)
        self.synthesis_thread.finished.connect(self.synthesis_thread.deleteLater)
        
        self.spinner = WaitingSpinnerDialog(self, text="正在合成视频, 请稍候...\n此过程不可中断。")
        self.start_time = time.time()
        self.spinner.show()
        self.synthesis_thread.start()

    def on_synthesis_finished(self, success, message, output_dir):
        self.spinner.accept()
        duration = time.time() - self.start_time
        
        if success:
            final_message = f"{message}\n\n总耗时: {duration:.2f} 秒"
            MessageBoxes.show_message(self, "合成成功", final_message, "success")
            QDesktopServices.openUrl(QUrl.fromLocalFile(output_dir))
        else:
            final_message = f"合成过程中发生错误:\n\n{message}\n\n总耗时: {duration:.2f} 秒"
            MessageBoxes.show_message(self, "合成失败", final_message, "warning")