# path: src/ui/views/selection_view.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, QPushButton, 
    QListView, QAbstractItemView
)
from PySide6.QtCore import Qt, Slot, Signal, QPoint, QItemSelectionModel
from PySide6.QtGui import QMouseEvent, QKeyEvent, QAction, QKeySequence

from ui.models.sentence_list_model import SentenceListModel
from ui.delegates.sentence_item_delegate import SentenceItemDelegate
from ui.widgets.list_header_widget import ListHeaderWidget
from ui.widgets.message_dialogs import MessageBoxes

class BaseSelectionListView(QListView):
    """
    一个包含通用选择逻辑的列表视图基类。
    通过发射信号与外部逻辑解耦，使其可在不同场景中复用。
    """
    range_selection_requested = Signal(int, int, bool) # start_row, end_row, select_state
    highlight_change_requested = Signal(int) # row

    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag_start_index = -1
        self._is_left_mouse_pressed = False
        self._is_right_mouse_pressed = False
        self._last_highlighted_row = -1

    def _get_index_near_pos(self, pos: QPoint):
        index = self.indexAt(pos)
        if index.isValid(): return index
        search_range = self.spacing() + 3
        for i in range(1, search_range):
            index_above = self.indexAt(pos - QPoint(0, i))
            if index_above.isValid(): return index_above
            index_below = self.indexAt(pos + QPoint(0, i))
            if index_below.isValid(): return index_below
        return self.indexAt(pos)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.MiddleButton: return
        index_obj = self._get_index_near_pos(event.position().toPoint())
        if not index_obj.isValid(): return

        if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            start_index = self._last_highlighted_row
            end_index = index_obj.row()
            if start_index < 0:
                start_index = end_index
            select_state = event.button() == Qt.MouseButton.LeftButton
            self.range_selection_requested.emit(start_index, end_index, select_state)
            self.highlight_change_requested.emit(end_index)
            self._last_highlighted_row = end_index
            return

        super().mousePressEvent(event)
        self._drag_start_index = index_obj.row()
        if event.button() == Qt.MouseButton.LeftButton: self._is_left_mouse_pressed = True
        elif event.button() == Qt.MouseButton.RightButton: self._is_right_mouse_pressed = True
        
        self.highlight_change_requested.emit(index_obj.row())
        self._last_highlighted_row = index_obj.row()

    def mouseMoveEvent(self, event: QMouseEvent):
        if not (self._is_left_mouse_pressed or self._is_right_mouse_pressed):
            super().mouseMoveEvent(event)
            return

        end_index_obj = self.indexAt(event.position().toPoint())
        if end_index_obj.isValid():
            end_index = end_index_obj.row()
            mode = self._is_left_mouse_pressed
            if self.model() and hasattr(self.model(), 'set_temp_selection_range'):
                self.model().set_temp_selection_range(self._drag_start_index, end_index, mode)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.MiddleButton:
            self._reset_mouse_state()
            super().mouseReleaseEvent(event)
            return

        super().mouseReleaseEvent(event)
        if self.model() and hasattr(self.model(), 'clear_temp_selection'):
            self.model().clear_temp_selection()
        if self._drag_start_index == -1:
            self._reset_mouse_state()
            return

        end_index_obj = self._get_index_near_pos(event.position().toPoint())
        if not end_index_obj.isValid():
             self._reset_mouse_state()
             return

        end_index = end_index_obj.row()
        start_index = self._drag_start_index
        select_state = event.button() == Qt.MouseButton.LeftButton
        
        self.range_selection_requested.emit(start_index, end_index, select_state)
        self.highlight_change_requested.emit(end_index)
        self._reset_mouse_state()

    def _reset_mouse_state(self):
        self._is_left_mouse_pressed = False
        self._is_right_mouse_pressed = False
        self._drag_start_index = -1

class CustomListView(BaseSelectionListView):
    def __init__(self, parent=None):
        super().__init__(parent)

class SelectionView(QWidget):
    ready_for_next = Signal(bool)

    def __init__(self, controller, model, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.project_model = model
        self._init_ui()
        self._create_actions()
        self._connect_signals()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(0)
        main_layout.addWidget(self._create_search_row())
        main_layout.addWidget(ListHeaderWidget())

        self.list_model = SentenceListModel(self.controller, self.project_model)
        self.list_view = CustomListView()
        self.list_view.setModel(self.list_model)
        self.list_view.setItemDelegate(SentenceItemDelegate(self))
        self.list_view.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.list_view.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.list_view.setMouseTracking(True)
        self.list_view.setSpacing(2)
        main_layout.addWidget(self.list_view, 1)
        main_layout.addWidget(self._create_stats_row())

    def _create_search_row(self) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 10)
        self.jump_to_highlight_btn = QPushButton("跳转到光标")
        layout.addWidget(self.jump_to_highlight_btn)
        index_label = QLabel("跳转到序号:")
        index_label.setStyleSheet("padding-left: 5px;")
        layout.addWidget(index_label)
        self.index_search_input = QLineEdit(placeholderText="例如: 123", fixedWidth=120)
        layout.addWidget(self.index_search_input)
        time_label = QLabel("跳转到时间:")
        time_label.setStyleSheet("padding-left: 5px;")
        layout.addWidget(time_label)
        self.time_search_input = QLineEdit(placeholderText="例如: 01:00:04.200", fixedWidth=180)
        layout.addWidget(self.time_search_input)
        layout.addStretch()
        self.select_all_btn = QPushButton("全选")
        layout.addWidget(self.select_all_btn)
        self.clear_all_btn = QPushButton("清空")
        layout.addWidget(self.clear_all_btn)
        layout.addWidget(QLabel("关键词搜索:"))
        self.text_search_input = QLineEdit(placeholderText="按Enter搜索正文...")
        self.search_status_label = QLabel("0/0")
        self.next_button = QPushButton("搜索")
        layout.addWidget(self.text_search_input)
        layout.addWidget(self.search_status_label)
        layout.addWidget(self.next_button)
        self.clear_search_btn = QPushButton("清空")
        layout.addWidget(self.clear_search_btn)
        return widget

    def _create_stats_row(self) -> QWidget:
        widget = QWidget(objectName="StatsRow")
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 8, 10, 8)
        self.stats_labels = {"selected": QLabel("已选: 0 句"), "chars": QLabel("总字数: 0"), "avg_chars": QLabel("平均: 0.0 字/句"), "duration": QLabel("总时长: 0:00:00"), "avg_duration": QLabel("平均: 0.000 秒/句")}
        for label in self.stats_labels.values():
            layout.addWidget(label)
            layout.addStretch()
        widget.setStyleSheet("QWidget#StatsRow { background-color: #2c3136; }")
        return widget

    def _create_actions(self):
        self.undo_action = QAction("撤销", self)
        self.undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        self.redo_action = QAction("重做", self)
        self.redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        self.addActions([self.undo_action, self.redo_action])

    def _connect_signals(self):
        self.list_view.range_selection_requested.connect(self.on_range_selection)
        self.list_view.highlight_change_requested.connect(self.on_highlight_change)
        self.jump_to_highlight_btn.clicked.connect(self.on_jump_to_highlighted)
        self.clear_search_btn.clicked.connect(self.on_clear_search)
        self.index_search_input.returnPressed.connect(self.on_jump_to_index)
        self.time_search_input.returnPressed.connect(self.on_jump_to_time)
        self.text_search_input.returnPressed.connect(self.on_search_text)
        self.text_search_input.textChanged.connect(lambda: self.next_button.setText("搜索"))
        self.next_button.clicked.connect(self.on_search_text)
        self.undo_action.triggered.connect(self.controller.undo)
        self.redo_action.triggered.connect(self.controller.redo)
        self.controller.signals.history_changed.connect(self.on_history_changed)
        self.controller.signals.highlight_changed.connect(self.on_highlight_changed_from_controller)
        self.controller.signals.statistics_updated.connect(self.on_update_stats)
        self.controller.signals.search_results_updated.connect(self.on_update_search_results)
        self.select_all_btn.clicked.connect(self.on_select_all_clicked)
        self.clear_all_btn.clicked.connect(self.on_clear_all_clicked)

    def showEvent(self, event):
        super().showEvent(event)
        self.enter_view()

    def enter_view(self):
        self.list_view.scheduleDelayedItemsLayout()
        self.controller.calculate_and_emit_statistics()
        if self.list_model.rowCount() > 0 and self.list_model.highlighted_index == -1:
            self.on_highlight_change(0)
        self.list_view.setFocus()


    def reset_view_state(self):
        self.list_view.scrollToTop()
        if self.list_model.rowCount() > 0:
            self.on_highlight_change(0)
        print("[信息] 筛选视图状态已重置 (已滚动到顶部并高亮首项)。")

    def jump_to_index(self, index: int):
        if 0 <= index < self.list_model.rowCount():
            self.list_view.scrollTo(self.list_model.index(index, 0), QAbstractItemView.ScrollHint.PositionAtCenter)
            self.on_highlight_change(index)

    @Slot(int, int, bool)
    def on_range_selection(self, start_row, end_row, select_state):
        self.controller.update_selection(start_row, end_row, select_state)
        self.controller.record_history_state(end_row)

    @Slot(int)
    def on_highlight_change(self, row):
        if self.list_model.highlighted_index != row:
            self.list_model.set_highlighted_index(row)
            self.list_view.selectionModel().setCurrentIndex(self.list_model.index(row, 0), QItemSelectionModel.NoUpdate)

    @Slot()
    def on_jump_to_highlighted(self):
        current_index = self.list_model.highlighted_index
        if current_index != -1: self.jump_to_index(current_index)

    @Slot()
    def on_clear_search(self):
        self.index_search_input.clear()
        self.time_search_input.clear()
        self.text_search_input.clear()
        self.controller.search_text("")

    @Slot()
    def on_jump_to_index(self):
        text = self.index_search_input.text().replace("#", "").strip()
        if text.isdigit(): self.jump_to_index(int(text) - 1)
    
    @Slot()
    def on_jump_to_time(self):
        time_str = self.time_search_input.text().strip()
        if time_str:
            index = self.controller.find_card_by_time(time_str)
            if index != -1: self.jump_to_index(index)

    @Slot()
    def on_search_text(self):
        query = self.text_search_input.text().strip()
        if not query:
            self.controller.search_text("")
            return
        if query == self.project_model.search_query and self.project_model.search_results:
            next_index = self.controller.get_next_search_result_index()
        else:
            next_index = self.controller.search_text(query)
        if next_index is not None and next_index != -1: self.jump_to_index(next_index)
    
    @Slot(dict)
    def on_update_stats(self, stats: dict):
        self.stats_labels["selected"].setText(f"已选: {stats['total_selected']} 句")
        self.stats_labels["chars"].setText(f"总字数: {stats['total_chars']}")
        self.stats_labels["avg_chars"].setText(f"平均: {stats['avg_chars']} 字/句")
        self.stats_labels["duration"].setText(f"总时长: {stats['total_duration']}")
        self.stats_labels["avg_duration"].setText(f"平均: {stats['avg_duration']} 秒/句")
        self.ready_for_next.emit(stats['total_selected'] > 0)

    @Slot()
    def on_update_search_results(self):
        total = len(self.project_model.search_results)
        current = self.project_model.search_current_index + 1 if total > 0 else 0
        self.search_status_label.setText(f"{current}/{total}")
        self.next_button.setText("下一个" if total > 0 else "搜索")
        
    @Slot(bool, bool)
    def on_history_changed(self, can_undo, can_redo):
        pass
        
    @Slot(int)
    def on_highlight_changed_from_controller(self, index):
        self.list_model.set_highlighted_index(index)
        self.jump_to_index(index)

    @Slot()
    def on_select_all_clicked(self):
        confirmed = MessageBoxes.ask_confirmation(
            self, "确认全选", 
            "此操作将选中所有句子。\n\n这可能会覆盖您当前的筛选结果，并影响“排序”页的已有序列。\n\n确定要继续吗？"
        )
        if confirmed:
            self.controller.select_all_items()
            
    @Slot()
    def on_clear_all_clicked(self):
        confirmed = MessageBoxes.ask_confirmation(
            self, "确认清空", 
            "此操作将取消所有句子的选中状态。\n\n这会清空您当前的筛选结果，并重置“排序”页。\n\n确定要继续吗？"
        )
        if confirmed:
            self.controller.clear_all_items()