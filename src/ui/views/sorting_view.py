# path: src/ui/views/sorting_view.py

from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, 
    QHBoxLayout, QPushButton, QFrame,
    QAbstractItemView
)
from PySide6.QtCore import Qt, Slot, QItemSelectionModel, QEvent
from PySide6.QtGui import QAction, QKeySequence, QKeyEvent

from .selection_view import BaseSelectionListView
from ui.delegates.sentence_item_delegate import SentenceItemDelegate
from ui.models.sorting_models import AvailableListModel, FinalListModel

class SortingListView(BaseSelectionListView):
    """为排序页定制的列表视图，增加了与控制器交互的上下文。"""
    def __init__(self, list_name, controller, model, parent=None):
        super().__init__(parent)
        self.list_name = list_name
        self.controller = controller
        self.qt_model = model

        self.range_selection_requested.connect(self._on_range_selection)
        self.highlight_change_requested.connect(self._on_highlight_change)

    @Slot(int, int, bool)
    def _on_range_selection(self, start_row, end_row, select_state):
        start = min(start_row, end_row)
        end = max(start_row, end_row)
        indices_to_change = {self.qt_model.get_original_index(i) for i in range(start, end + 1)}
        indices_to_change.discard(-1)
        if indices_to_change:
            self.controller.update_sorting_selection(self.list_name, indices_to_change, select_state)

    @Slot(int)
    def _on_highlight_change(self, row):
        original_index = self.qt_model.get_original_index(row)
        if original_index != -1:
            # BUG-FIX: 同步视图内部的选择模型光标，以修复Shift键选择功能
            current_model_index = self.qt_model.index(row, 0)
            self.selectionModel().setCurrentIndex(current_model_index, QItemSelectionModel.NoUpdate)
            self.controller.set_sorting_highlight(self.list_name, original_index)

class SortingView(QWidget):
    def __init__(self, controller, model, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.project_model = model
        self._init_ui()
        self._create_actions()
        self._connect_signals()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        content_layout = QHBoxLayout()
        content_layout.setSpacing(10)
        content_layout.setContentsMargins(0,0,0,0)

        self.available_list_model = AvailableListModel(self.project_model)
        self.final_list_model = FinalListModel(self.project_model)

        available_panel = self._create_list_panel("未排序句", self.available_list_model, "available")
        final_panel = self._create_list_panel("最终序列", self.final_list_model, "final")
        
        content_layout.addWidget(available_panel, 1)
        content_layout.addWidget(self._create_transfer_panel())
        content_layout.addWidget(final_panel, 1)
        
        main_layout.addLayout(content_layout, 1)
        main_layout.addWidget(self._create_stats_row())

        # 安装事件过滤器以捕获子列表的键盘事件
        self.available_list_view.installEventFilter(self)
        self.final_list_view.installEventFilter(self)

    def _create_list_panel(self, title, qt_model, list_name):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(5)
        
        label = QLabel(title)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        list_view = SortingListView(list_name, self.controller, qt_model)
        list_view.setModel(qt_model)
        list_view.setItemDelegate(SentenceItemDelegate(self))
        list_view.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        list_view.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        list_view.setSpacing(2)
        
        layout.addWidget(label)
        layout.addWidget(list_view)
        
        # 将列表视图保存为属性，方便后续访问
        setattr(self, f"{list_name}_list_view", list_view)

        return widget

    def _create_transfer_panel(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(15)

        self.to_start_btn = QPushButton("-> 开头 (S)")
        self.to_cursor_btn = QPushButton("-> 光标 (D)")
        self.to_end_btn = QPushButton("-> 结尾 (F)")
        self.return_btn = QPushButton("<- 归位 (G)")

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)

        layout.addStretch()
        layout.addWidget(self.to_start_btn)
        layout.addWidget(self.to_cursor_btn)
        layout.addWidget(self.to_end_btn)
        layout.addSpacing(30)
        layout.addWidget(separator)
        layout.addSpacing(30)
        layout.addWidget(self.return_btn)
        layout.addStretch()
        return widget

    def _create_stats_row(self) -> QWidget:
        widget = QWidget(objectName="StatsRow")
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 8, 10, 8)
        self.stats_labels = {
            "finalized": QLabel("最终: 0 句"),
            "chars": QLabel("总字数: 0"),
            "avg_chars": QLabel("平均: 0.0 字/句"),
            "duration": QLabel("总时长: 0:00:00"),
            "avg_duration": QLabel("平均: 0.000 秒/句")
        }
        for label in self.stats_labels.values():
            layout.addWidget(label)
            layout.addStretch()
        widget.setStyleSheet("QWidget#StatsRow { background-color: #2c3136; }")
        return widget

    def _create_actions(self):
        """为排序视图创建并添加撤销/重做操作。"""
        self.undo_action = QAction("撤销", self)
        self.undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        self.redo_action = QAction("重做", self)
        self.redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        self.addActions([self.undo_action, self.redo_action])

    def _connect_signals(self):
        self.to_start_btn.clicked.connect(lambda: self.controller.transfer_items_to_final('start'))
        self.to_cursor_btn.clicked.connect(lambda: self.controller.transfer_items_to_final('cursor'))
        self.to_end_btn.clicked.connect(lambda: self.controller.transfer_items_to_final('end'))
        self.return_btn.clicked.connect(self.controller.return_items_from_final)
        
        self.controller.signals.sorting_data_changed.connect(self.on_sorting_data_changed)
        self.controller.signals.sorting_statistics_updated.connect(self.on_update_stats)

        self.undo_action.triggered.connect(self.controller.undo_sorting)
        self.redo_action.triggered.connect(self.controller.redo_sorting)
        self.controller.signals.sorting_history_changed.connect(self.on_history_changed)

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.KeyPress and watched in [self.available_list_view, self.final_list_view]:
            self.keyPressEvent(event)
            return True
        return super().eventFilter(watched, event)

    def keyPressEvent(self, event: QKeyEvent):
        """处理排序页的自定义快捷键。"""
        key = event.key()
        if key == Qt.Key.Key_Escape:
            self.controller.clear_all_sorting_selections()
        elif key == Qt.Key.Key_S:
            self.to_start_btn.click()
        elif key == Qt.Key.Key_D:
            self.to_cursor_btn.click()
        elif key == Qt.Key.Key_F:
            self.to_end_btn.click()
        elif key == Qt.Key.Key_G:
            self.return_btn.click()
        else:
            super().keyPressEvent(event)

    def enter_view(self):
        self.controller.initialize_sorting_data()
        self.controller.refresh_sorting_history_status()
    
    def reset_view_state(self):
        self.project_model.reset_sorting_state()
        self.on_sorting_data_changed()
        self.controller.refresh_sorting_history_status()
        self.controller.calculate_and_emit_sorting_statistics()
        print("排序视图状态已重置。")

    @Slot()
    def on_sorting_data_changed(self):
        self.available_list_model.update_data()
        self.final_list_model.update_data()

    @Slot(dict)
    def on_update_stats(self, stats: dict):
        self.stats_labels["finalized"].setText(f"最终: {stats['total_finalized']} 句")
        self.stats_labels["chars"].setText(f"总字数: {stats['total_chars']}")
        self.stats_labels["avg_chars"].setText(f"平均: {stats['avg_chars']} 字/句")
        self.stats_labels["duration"].setText(f"总时长: {stats['total_duration']}")
        self.stats_labels["avg_duration"].setText(f"平均: {stats['avg_duration']} 秒/句")

    @Slot(bool, bool)
    def on_history_changed(self, can_undo, can_redo):
        """根据控制器的信号更新撤销/重做按钮的可用状态。"""
        # self.undo_action.setEnabled(can_undo)
        # self.redo_action.setEnabled(can_redo)
        pass