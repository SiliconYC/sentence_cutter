# path: src/ui/models/sentence_list_model.py

from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt, Slot

class SentenceListModel(QAbstractListModel):
    """
    为句子列表视图提供数据的Qt模型。
    它封装了项目模型中的字幕数据和选择状态，并能在数据变化时通知视图更新。
    """
    SubtitleDataRole = Qt.ItemDataRole.UserRole + 1
    SelectionStateRole = Qt.ItemDataRole.UserRole + 2
    HighlightStateRole = Qt.ItemDataRole.UserRole + 3
    SearchHighlightRole = Qt.ItemDataRole.UserRole + 4
    TempSelectionStateRole = Qt.ItemDataRole.UserRole + 5 

    def __init__(self, controller, model, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.project_model = model
        self.highlighted_index = -1
        self.temp_selection_state = []
        self._temp_select_mode = True
        self._last_temp_range = (-1, -1)

        self.controller.signals.selection_changed.connect(self.on_selection_changed)
        self.controller.signals.search_results_updated.connect(self.on_search_results_updated)

    def rowCount(self, parent=QModelIndex()):
        count = len(self.project_model.subtitle_data)
        if len(self.temp_selection_state) != count:
            self.temp_selection_state = [False] * count
        return count

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < self.rowCount()):
            return None

        row = index.row()
        
        if role == self.SubtitleDataRole:
            return self.project_model.subtitle_data[row]
        elif role == self.SelectionStateRole:
            return self.project_model.selection_state[row]
        elif role == self.HighlightStateRole:
            return row == self.highlighted_index
        elif role == self.TempSelectionStateRole:
            return (self.temp_selection_state[row], self._temp_select_mode)
        elif role == self.SearchHighlightRole:
            ranges = []
            for card_idx, start, length in self.project_model.search_results:
                if card_idx == row:
                    ranges.append((start, length))
            return ranges
        elif role == Qt.ToolTipRole:
            return self.project_model.subtitle_data[row]['text']
        
        return None

    def set_highlighted_index(self, index: int):
        if self.highlighted_index != index:
            old_index = self.highlighted_index
            self.highlighted_index = index
            if old_index != -1:
                idx = self.index(old_index, 0)
                self.dataChanged.emit(idx, idx, [self.HighlightStateRole])
            if self.highlighted_index != -1:
                new_idx = self.index(self.highlighted_index, 0)
                self.dataChanged.emit(new_idx, new_idx, [self.HighlightStateRole])
    
    def set_temp_selection_range(self, start: int, end: int, mode: bool):
        """
        优化后的临时选择方法，可大幅减少UI刷新次数，解决闪烁问题。
        """
        self._temp_select_mode = mode
        current_range = (-1, -1)
        if start != -1 and end != -1:
            s, e = min(start, end), max(start, end)
            current_range = (s, e)

        if current_range == self._last_temp_range and self._temp_select_mode == mode:
            return
            
        old_s, old_e = self._last_temp_range
        new_s, new_e = current_range

        for i in range(self.rowCount()):
            is_in_new_range = new_s != -1 and new_s <= i <= new_e
            self.temp_selection_state[i] = is_in_new_range

        update_s, update_e = -1, -1
        if old_s == -1:
            update_s, update_e = new_s, new_e
        elif new_s == -1:
            update_s, update_e = old_s, old_e
        else:
            update_s = min(old_s, new_s)
            update_e = max(old_e, new_e)

        if update_s != -1:
            start_idx = self.index(update_s, 0)
            end_idx = self.index(update_e, 0)
            self.dataChanged.emit(start_idx, end_idx, [self.TempSelectionStateRole])
        
        self._last_temp_range = current_range

    def clear_temp_selection(self):
        self.set_temp_selection_range(-1, -1, True)

    @Slot(int, int)
    def on_selection_changed(self, start_index, end_index):
        start = self.index(start_index, 0)
        end = self.index(end_index, 0)
        self.dataChanged.emit(start, end, [self.SelectionStateRole])
    
    @Slot()
    def on_search_results_updated(self):
        self.dataChanged.emit(self.index(0, 0), self.index(self.rowCount() - 1, 0), [self.SearchHighlightRole])