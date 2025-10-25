# path: src/ui/models/sorting_models.py

from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt
from ui.models.sentence_list_model import SentenceListModel

class BaseSortingModel(QAbstractListModel):
    """为排序页的两个列表提供数据模型的基类。"""
    def __init__(self, project_model, parent=None):
        super().__init__(parent)
        self.project_model = project_model
        self._items = []
        self._original_indices = []
        
        # 用于拖拽临时选择状态
        self.temp_selection_state = []
        self._temp_select_mode = True
        self._last_temp_range = (-1, -1)

    def rowCount(self, parent=QModelIndex()):
        return len(self._items)

    def get_original_index(self, row):
        if 0 <= row < len(self._original_indices):
            return self._original_indices[row]
        return -1

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < self.rowCount()):
            return None
        
        row = index.row()
        original_index = self._original_indices[row]

        if role == SentenceListModel.SubtitleDataRole:
            return self._items[row]
        elif role == SentenceListModel.SelectionStateRole:
            return self._is_selected(original_index)
        elif role == SentenceListModel.HighlightStateRole:
            return self._is_highlighted(original_index)
        elif role == SentenceListModel.TempSelectionStateRole:
            return (self.temp_selection_state[row], self._temp_select_mode)
        elif role == Qt.ToolTipRole:
            return self._items[row]['text']
        
        return None
    
    def set_temp_selection_range(self, start: int, end: int, mode: bool):
        self._temp_select_mode = mode
        current_range = (-1, -1)
        if start != -1 and end != -1:
            s, e = min(start, end), max(start, end)
            current_range = (s, e)
        if current_range == self._last_temp_range and self._temp_select_mode == mode: return
        old_s, old_e = self._last_temp_range
        new_s, new_e = current_range
        for i in range(self.rowCount()):
            self.temp_selection_state[i] = new_s != -1 and new_s <= i <= new_e
        update_s, update_e = (min(old_s, new_s), max(old_e, new_e)) if old_s != -1 and new_s != -1 else (new_s, new_e) if old_s == -1 else (old_s, old_e)
        if update_s != -1:
            self.dataChanged.emit(self.index(update_s, 0), self.index(update_e, 0), [SentenceListModel.TempSelectionStateRole])
        self._last_temp_range = current_range

    def clear_temp_selection(self):
        self.set_temp_selection_range(-1, -1, True)

    def _is_selected(self, original_index): raise NotImplementedError
    def _is_highlighted(self, original_index): raise NotImplementedError

    def update_data(self):
        self.beginResetModel()
        self._load_items()
        if len(self.temp_selection_state) != self.rowCount():
            self.temp_selection_state = [False] * self.rowCount()
        self.endResetModel()

    def _load_items(self): raise NotImplementedError

class AvailableListModel(BaseSortingModel):
    """“未排序句”列表的数据模型。"""
    def _is_selected(self, original_index): return original_index in self.project_model.available_selection
    def _is_highlighted(self, original_index): return original_index == self.project_model.available_highlight
    def _load_items(self):
        all_selected = {i for i, selected in enumerate(self.project_model.selection_state) if selected}
        finalized = set(self.project_model.final_sequence)
        available_indices = sorted(list(all_selected - finalized))
        self._original_indices = available_indices
        self._items = [self.project_model.subtitle_data[i] for i in available_indices]

class FinalListModel(BaseSortingModel):
    """“最终序列”列表的数据模型。"""
    def _is_selected(self, original_index): return original_index in self.project_model.final_selection
    def _is_highlighted(self, original_index): return original_index == self.project_model.final_highlight
    def _load_items(self):
        self._original_indices = self.project_model.final_sequence.copy()
        self._items = [self.project_model.subtitle_data[i] for i in self._original_indices]