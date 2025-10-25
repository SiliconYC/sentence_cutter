# path: src/ui/delegates/sentence_item_delegate.py

import html
from PySide6.QtWidgets import QStyledItemDelegate
from PySide6.QtGui import QColor, QPen, QTextDocument, QFontMetrics, QFont
from PySide6.QtCore import Qt, QRect, QSize
from ui.models.sentence_list_model import SentenceListModel

class SentenceItemDelegate(QStyledItemDelegate):
    """
    负责在句子列表视图中绘制每个条目。
    取代了原有的 SentenceCard 控件，提供了更高的性能和渲染控制。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.color_background = QColor("#31363B")
        self.color_background_selected = QColor("#003d5b")
        self.color_border_highlighted = QColor("#f9ca24")
        self.color_text_index = QColor("#00a8ff")
        self.color_text_time = QColor("#9e9e9e")
        self.color_text_main = QColor("#CCCCCC")
        self.color_text_search_bg = QColor("#f9ca24")
        self.color_text_search_fg = QColor("#3d3d3d")

        self.font_index = QFont("Arial", 14, QFont.Weight.Bold)
        self.font_time = QFont("Arial", 12)
        self.font_main = QFont("Arial", 14)
        
        self.padding = 10
        self.spacing = 10
        self.col_widths = {'index': 60, 'start': 100, 'end': 100}
        self.fixed_height = 45

    def paint(self, painter, option, index):
        painter.save()
        
        is_selected = index.data(SentenceListModel.SelectionStateRole)
        is_highlighted = index.data(SentenceListModel.HighlightStateRole)
        
        temp_selection_data = index.data(SentenceListModel.TempSelectionStateRole)
        if temp_selection_data is None:
            is_temp_selected, temp_select_mode = False, True
        else:
            is_temp_selected, temp_select_mode = temp_selection_data

        data = index.data(SentenceListModel.SubtitleDataRole)
        search_ranges = index.data(SentenceListModel.SearchHighlightRole)

        bg_color = self.color_background
        if is_temp_selected:
            bg_color = self.color_background_selected if temp_select_mode else self.color_background
        elif is_selected:
            bg_color = self.color_background_selected
        painter.fillRect(option.rect, bg_color)

        if is_highlighted:
            pen = QPen(self.color_border_highlighted, 2)
            painter.setPen(pen)
            painter.drawRect(option.rect.adjusted(1, 1, -1, -1))

        item_center_y = option.rect.y() + option.rect.height() / 2
        manual_offset = 2 

        fm_index = QFontMetrics(self.font_index)
        y_index = item_center_y - fm_index.height() / 2 + fm_index.ascent() - fm_index.descent() + manual_offset
        painter.setPen(self.color_text_index)
        painter.setFont(self.font_index)
        rect_index = QRect(option.rect.x() + self.padding, int(y_index - fm_index.ascent()), self.col_widths['index'], fm_index.height())
        painter.drawText(rect_index, Qt.AlignmentFlag.AlignCenter, f"#{data['index']}")

        current_x = self.padding + self.col_widths['index'] + self.spacing

        fm_time = QFontMetrics(self.font_time)
        y_time = item_center_y - fm_time.height() / 2 + fm_time.ascent() - fm_time.descent() + manual_offset + 1
        painter.setPen(self.color_text_time)
        painter.setFont(self.font_time)
        rect_start = QRect(option.rect.x() + current_x, int(y_time - fm_time.ascent()), self.col_widths['start'], fm_time.height())
        painter.drawText(rect_start, Qt.AlignmentFlag.AlignCenter, data['start'])
        current_x += self.col_widths['start'] + self.spacing
        
        rect_end = QRect(option.rect.x() + current_x, int(y_time - fm_time.ascent()), self.col_widths['end'], fm_time.height())
        painter.drawText(rect_end, Qt.AlignmentFlag.AlignCenter, data['end'])
        current_x += self.col_widths['end'] + self.spacing

        text_width = option.rect.width() - current_x - self.padding
        rect_text = QRect(option.rect.x() + current_x, option.rect.y(), text_width, option.rect.height())
        self.draw_item_text(painter, rect_text, data['text'], search_ranges)
        
        painter.restore()

    def sizeHint(self, option, index):
        return QSize(option.rect.width(), self.fixed_height)
    
    def draw_item_text(self, painter, rect, text, ranges):
        painter.save()
        painter.setFont(self.font_main)
        
        # 如果存在搜索高亮范围，则必须使用富文本路径（QTextDocument）
        if ranges:
            doc = QTextDocument()
            doc.setDefaultFont(painter.font())
            doc.setTextWidth(rect.width())
            
            highlight_format = f"background-color: {self.color_text_search_bg.name()}; color: {self.color_text_search_fg.name()};"
            html_body = ""
            last_pos = 0
            for start, length in sorted(ranges):
                pre_match = html.escape(text[last_pos:start]).replace('\n', '<br>')
                match = html.escape(text[start:start+length]).replace('\n', '<br>')
                html_body += pre_match
                html_body += f"<span style='{highlight_format}'>{match}</span>"
                last_pos = start + length
            post_match = html.escape(text[last_pos:]).replace('\n', '<br>')
            html_body += post_match
            
            full_html = f"<div style='color: {self.color_text_main.name()};'>{html_body}</div>"
            doc.setHtml(full_html)

            # 垂直居中
            painter.translate(rect.left(), rect.top() + (rect.height() - doc.size().height()) / 2)
            doc.drawContents(painter)
            
        # 对于无高亮的普通文本，使用 QFontMetrics 和 painter.drawText 高效处理
        else:
            single_line_text = text.replace('\n', ' ')
            painter.setPen(self.color_text_main)

            # --- 修改开始 ---
            # 1. 获取当前字体的 FontMetrics
            fm = QFontMetrics(painter.font())

            # 2. 使用 elidedText 方法获取带省略号的文本
            #    它会根据矩形宽度 rect.width() 自动判断是否需要以及在哪里添加 "..."
            elided_text = fm.elidedText(single_line_text, Qt.TextElideMode.ElideRight, rect.width())
            
            # 3. 设置对齐方式，不再需要省略号标志
            flags = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
            
            # 4. 绘制已经处理好的带省略号的文本
            painter.drawText(rect, flags, elided_text)
            # --- 修改结束 ---

        painter.restore()