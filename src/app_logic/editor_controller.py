# path: src/app_logic/editor_controller.py

# ◔ 说明: 编辑器流程控制器，负责处理三步式编辑流程中的业务逻辑。

import os
import re
import bisect
import time
import json
import traceback
from datetime import timedelta, datetime
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl, Signal, QObject

from core.media_parser import MediaParser
from utils.app_config import SOURCE_DIR_NAME, CLIPS_DIR_NAME, OUTPUT_DIR_NAME, INTERMEDIATE_DIR_NAME
from ui.widgets.message_dialogs import MessageBoxes
from core.video_processor import VideoProcessor
from core.video_parser import VideoParser


class EditorControllerSignals(QObject):
    # 当选择状态改变时发出信号，传递 (start_index, end_index)
    selection_changed = Signal(int, int)
    # 当统计数据需要更新时发出
    statistics_updated = Signal(dict)
    # 当搜索结果更新时发出
    search_results_updated = Signal()
    # 当历史记录状态改变时发出 (可否撤销, 可否重做)
    history_changed = Signal(bool, bool)
    # 通知UI高亮索引因历史记录操作而改变
    highlight_changed = Signal(int)
    # --- 排序页信号 ---
    # 当最终序列或其选择/高亮状态改变时发出
    sorting_data_changed = Signal()
    # 当排序页历史记录状态改变时发出 (可否撤销, 可否重做)
    sorting_history_changed = Signal(bool, bool)
    # 当排序页统计数据需要更新时发出
    sorting_statistics_updated = Signal(dict)


class SynthesisWorker(QObject):
    finished = Signal(bool, str, str) # success, message, output_dir

    def __init__(self, project_model, video_paths, parent=None):
        super().__init__(parent)
        self.model = project_model
        self.video_paths = video_paths
        self.video_processor = VideoProcessor()
        self.video_parser = VideoParser()

    def run(self):
        print("\n\n[开始] 视频合成后台任务开始")
        start_time = time.time()
        try:
            # --- 1. 准备路径和数据 ---
            project_path = self.model.project_path
            clips_root_dir = os.path.join(project_path, CLIPS_DIR_NAME)
            output_root_dir = os.path.join(project_path, OUTPUT_DIR_NAME)
            os.makedirs(clips_root_dir, exist_ok=True)
            os.makedirs(output_root_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            synthesis_output_dir = os.path.join(output_root_dir, timestamp)
            os.makedirs(synthesis_output_dir, exist_ok=True)

            srt_total_duration = self.model.srt_meta.get('total_duration', 0)
            if srt_total_duration == 0:
                raise ValueError("无法获取SRT字幕总时长，无法继续。")

            # --- 2. 校验所有输入视频 ---
            print("[步骤 1/5] 校验输入视频...")
            valid_videos_meta = []
            for video_path in self.video_paths:
                duration = self.video_parser.get_video_duration(video_path)
                if duration < srt_total_duration:
                    msg = f"视频 '{os.path.basename(video_path)}' (时长: {duration:.2f}s) 短于字幕总时长 ({srt_total_duration:.2f}s)，已跳过。"
                    print(f"[警告] {msg}")
                    continue
                
                meta = self.video_parser.parse(video_path)
                if meta:
                    valid_videos_meta.append(meta)
            
            if not valid_videos_meta:
                raise RuntimeError("所有提供的视频素材都不合格（时长不足），合成中止。")

            # --- 3. 预处理时间和筛选最终序列数据 ---
            print("[步骤 2/5] 预处理字幕时间...")
            preprocessed_srt = self.video_processor.preprocess_srt_times(
                self.model.subtitle_data,
                srt_total_duration
            )
            final_sequence_indices = self.model.final_sequence
            final_sequence_data = [preprocessed_srt[i] for i in final_sequence_indices]

            # --- 4. 循环处理每个合格的视频 ---
            for video_meta in valid_videos_meta:
                source_video_path = video_meta['filename']
                source_video_basename = os.path.basename(source_video_path)
                print(f"\n--- [开始处理] '{source_video_basename}' ---")

                # 为每个视频创建独立的缓存子目录
                clips_dir = os.path.join(clips_root_dir, source_video_basename)
                os.makedirs(clips_dir, exist_ok=True)
                manifest_path = os.path.join(clips_dir, "clip_manifest.json")

                # 剪切片段
                print(f"[步骤 3/5] 正在为 '{source_video_basename}' 剪切片段...")
                clip_paths = self.video_processor.cut_and_save_clips(
                    source_video_path,
                    video_meta['size'],
                    final_sequence_data,
                    clips_dir,
                    manifest_path
                )
                
                if not clip_paths or len(clip_paths) != len(final_sequence_data):
                     raise RuntimeError(f"为 '{source_video_basename}' 生成片段失败或数量不匹配。")
                
                # 拼接视频
                print(f"[步骤 4/5] 正在为 '{source_video_basename}' 拼接最终视频...")
                output_video_name = f"{os.path.splitext(source_video_basename)[0]}_output.mp4"
                output_video_path = os.path.join(synthesis_output_dir, output_video_name)
                self.video_processor.concatenate_clips(clip_paths, output_video_path)
                print(f"--- [完成处理] '{source_video_basename}' ---")
            
            total_duration = time.time() - start_time
            print(f"\n[信息] 所有视频处理完成, 总耗时: {total_duration:.2f} 秒。")

            # --- 5. 创建 Excel 映射表 ---
            print("[步骤 5/5] 创建 Excel 映射表...")
            excel_path = os.path.join(synthesis_output_dir, f"{timestamp}_精剪参考表.xlsx")
            original_sequence_data = [self.model.subtitle_data[i] for i in final_sequence_indices]
            
            self.video_processor.create_mapping_excel(
                valid_videos_meta,
                final_sequence_data,
                original_sequence_data,
                excel_path,
                synthesis_output_dir,
                total_duration
            )
            
            print("[完成] 所有任务完成。")
            self.finished.emit(True, f"视频已成功导出至新文件夹。", synthesis_output_dir)
            
        except Exception as e:
            error_details = traceback.format_exc()
            print(f"[错误] 合成失败: {e}\n{error_details}")
            self.finished.emit(False, str(e), "")
        print("[结束] 视频合成后台任务结束")


class EditorController:
    """
    处理编辑器视图（创建、筛选、排序）内部的逻辑。
    """
    def __init__(self, model, main_window):
        self.model = model
        self.main_window = main_window # 用于显示弹窗
        self.media_parser = MediaParser()
        self.signals = EditorControllerSignals()
        self.state_filename = "project_state.json"
        self.meta_filename = "video_meta.json"
        self.srt_data_filename = "subtitle_data.json"

    def open_source_directory(self):
        """打开当前项目的源文件目录。"""
        if not self.model.project_path:
            return
        
        source_path = os.path.join(self.model.project_path, SOURCE_DIR_NAME)
        QDesktopServices.openUrl(QUrl.fromLocalFile(source_path))

    def initialize_project_media(self):
        """执行项目初始化并将解析结果保存到硬盘。"""
        if not self.model.project_path:
            return False, "项目路径未设置。"

        source_path = os.path.join(self.model.project_path, SOURCE_DIR_NAME)
        
        validation_result, message = self.media_parser.validate_source_directory(source_path)
        if not validation_result:
            return False, message

        try:
            # 1. 解析媒体文件
            video_meta, subtitle_data = self.media_parser.parse(source_path)
            
            # 2. 将解析结果保存到硬盘
            intermediate_dir = os.path.join(self.model.project_path, INTERMEDIATE_DIR_NAME)
            meta_path = os.path.join(intermediate_dir, self.meta_filename)
            srt_data_path = os.path.join(intermediate_dir, self.srt_data_filename)
            
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(video_meta, f, indent=4)
            with open(srt_data_path, 'w', encoding='utf-8') as f:
                json.dump(subtitle_data, f, indent=4)
                
            # 3. 加载到内存模型并清理旧状态
            self.model.load_data(video_meta, subtitle_data)
            self.signals.history_changed.emit(False, False)
            self.signals.sorting_history_changed.emit(False, False)
            self.calculate_and_emit_statistics()
            
            state_path = os.path.join(intermediate_dir, self.state_filename)
            if os.path.exists(state_path):
                try:
                    os.remove(state_path)
                    print(f"[信息] 因重新初始化，已删除旧的项目状态文件: {state_path}")
                except OSError as e:
                    print(f"[警告] 无法删除旧的项目状态文件: {e}")

            return True, "项目初始化成功！"
        except Exception as e:
            return False, f"解析媒体文件时发生错误：\n{e}"

    def update_selection(self, start_index, end_index, select_state):
        """更新模型中的选择状态，并触发统计更新。"""
        if not self.model.is_initialized:
            return

        start = min(start_index, end_index)
        end = max(start_index, end_index)
        start = max(0, start)
        end = min(len(self.model.selection_state) - 1, end)
        
        changed = False
        for i in range(start, end + 1):
            if self.model.selection_state[i] != select_state:
                self.model.selection_state[i] = select_state
                changed = True
        
        if changed:
            self.signals.selection_changed.emit(start, end)
            self.calculate_and_emit_statistics()
    
    def select_all_items(self, highlight_at_end=False):
        """全选所有项目。"""
        self.model.selection_state = [True] * len(self.model.subtitle_data)
        self.signals.selection_changed.emit(0, len(self.model.selection_state) - 1)
        self.calculate_and_emit_statistics()
        new_highlight = len(self.model.subtitle_data) - 1 if highlight_at_end else 0
        self.record_history_state(new_highlight)
        self.signals.highlight_changed.emit(new_highlight)

    def clear_all_items(self):
        """清空所有选择。"""
        self.model.selection_state = [False] * len(self.model.subtitle_data)
        self.signals.selection_changed.emit(0, len(self.model.selection_state) - 1)
        self.calculate_and_emit_statistics()
        self.record_history_state(0)
        self.signals.highlight_changed.emit(0)


    def calculate_and_emit_statistics(self):
        """计算统计数据并发出信号。"""
        total_selected = sum(self.model.selection_state)
        total_chars = 0
        total_duration = 0.0
        for i, selected in enumerate(self.model.selection_state):
            if selected:
                item = self.model.subtitle_data[i]
                total_chars += len(item['text'])
                total_duration += item['duration']
        avg_chars = total_chars / total_selected if total_selected > 0 else 0
        avg_duration = total_duration / total_selected if total_selected > 0 else 0
        total_time_str = str(timedelta(seconds=int(total_duration)))
        stats = {
            "total_selected": total_selected,
            "total_chars": total_chars,
            "avg_chars": f"{avg_chars:.1f}",
            "total_duration": total_time_str,
            "avg_duration": f"{avg_duration:.3f}"
        }
        self.signals.statistics_updated.emit(stats)

    def calculate_and_emit_sorting_statistics(self):
        """计算排序页的统计数据并发出信号。"""
        if not self.model.is_initialized:
            return
            
        final_count = len(self.model.final_sequence)
        total_chars = 0
        total_duration = 0.0
        
        for index in self.model.final_sequence:
            item = self.model.subtitle_data[index]
            total_chars += len(item['text'])
            total_duration += item['duration']
            
        avg_chars = total_chars / final_count if final_count > 0 else 0
        avg_duration = total_duration / final_count if final_count > 0 else 0
        total_time_str = str(timedelta(seconds=int(total_duration)))
        
        stats = {
            "total_finalized": final_count,
            "total_chars": total_chars,
            "avg_chars": f"{avg_chars:.1f}",
            "total_duration": total_time_str,
            "avg_duration": f"{avg_duration:.3f}"
        }
        self.signals.sorting_statistics_updated.emit(stats)


    def find_card_by_time(self, time_str: str) -> int:
        """根据时间字符串查找卡片索引。"""
        target_sec = -1
        
        time_str = time_str.replace(' ', '').replace('：', ':')
        
        if ':' not in time_str:
            try:
                target_sec = float(time_str)
            except ValueError:
                pass
        if target_sec < 0:
            try:
                time_str = time_str.replace(',', '.', 1)
                parts = time_str.split('.')
                hms_part = parts[0]
                ms_part = parts[1] if len(parts) > 1 else "0"
                hms_parts = hms_part.split(':')
                sec = 0
                multiplier = 1
                for part in reversed(hms_parts):
                    sec += int(part) * multiplier
                    multiplier *= 60
                ms = int(ms_part.ljust(3, '0')[:3])
                target_sec = sec + ms / 1000.0
            except (ValueError, IndexError):
                pass
        if target_sec < 0:
            MessageBoxes.show_message(
                self.main_window, 
                "格式错误", 
                """无法解析时间。

有效格式如下：

1. 带毫秒的时间码, 如 1:02:03.456
2. 不带毫秒的时间码, 如 1:02:03
3. 简化为小时和分钟的时间码, 如 1:02
4. 带毫秒的秒数, 如 3604.2
5. 整数秒数, 如 3604""",
                "warning"
            )
            return -1
            
        srt_duration = self.model.srt_meta.get('total_duration', float('inf'))
        if target_sec > srt_duration:
            MessageBoxes.show_message(self.main_window, "超出范围", "输入的时间超出了字幕总时长。", "info")
            return len(self.model.subtitle_data) - 1
            
        start_times = [item['start_seconds'] for item in self.model.subtitle_data]
        pos = bisect.bisect_right(start_times, target_sec) - 1
        if pos >= 0 and self.model.subtitle_data[pos]['start_seconds'] <= target_sec <= self.model.subtitle_data[pos]['end_seconds']:
            return pos
        else:
            return max(0, pos)
            
    def search_text(self, query: str):
        """执行新的文本搜索, 空查询会清空搜索结果。"""
        self.model.reset_search_state()
        if not query:
            self.signals.search_results_updated.emit()
            return -1
        
        self.model.search_query = query
        results = []
        for i, item in enumerate(self.model.subtitle_data):
            for match in re.finditer(re.escape(query), item['text'], re.IGNORECASE):
                results.append((i, match.start(), len(query)))
        
        self.model.search_results = results
        if results:
            self.model.search_current_index = 0
        
        self.signals.search_results_updated.emit()
        return self.get_current_search_result_index()

    def get_next_search_result_index(self) -> int:
        """循环跳转到下一个搜索结果。"""
        if not self.model.search_results:
            return -1
        current = self.model.search_current_index
        current = (current + 1) % len(self.model.search_results)
        self.model.search_current_index = current
        self.signals.search_results_updated.emit()
        return self.get_current_search_result_index()

    def get_current_search_result_index(self) -> int:
        """获取当前高亮结果所在的卡片索引。"""
        if self.model.search_current_index != -1:
            return self.model.search_results[self.model.search_current_index][0]
        return -1

    def record_history_state(self, highlighted_index: int):
        current_state = (self.model.selection_state.copy(), highlighted_index)
        last_recorded_state = self.model.state_history[self.model.history_index]
        if current_state[0] == last_recorded_state[0] and current_state[1] == last_recorded_state[1]: return
        if self.model.history_index < len(self.model.state_history) - 1:
            self.model.state_history = self.model.state_history[:self.model.history_index + 1]
        self.model.state_history.append(current_state)
        self.model.history_index += 1
        if len(self.model.state_history) > self.model.MAX_HISTORY_SIZE:
            self.model.state_history.pop(0)
            self.model.history_index -= 1
        self._emit_history_change()

    def undo(self):
        if self.model.history_index > 0:
            self.model.history_index -= 1
            self._apply_history_state()
        else:
            MessageBoxes.show_message(self.main_window, "提示", "已是第一条记录。", "warning")

    def redo(self):
        if self.model.history_index < len(self.model.state_history) - 1:
            self.model.history_index += 1
            self._apply_history_state()
        else:
            MessageBoxes.show_message(self.main_window, "提示", "已是最后一条记录。", "warning")


    def _apply_history_state(self):
        selection_state, highlighted_index = self.model.state_history[self.model.history_index]
        self.model.selection_state = selection_state.copy()
        self.signals.selection_changed.emit(0, len(self.model.selection_state) - 1)
        self.signals.highlight_changed.emit(highlighted_index)
        self.calculate_and_emit_statistics()
        self._emit_history_change()

    def _emit_history_change(self):
        can_undo = self.model.history_index > 0
        can_redo = self.model.history_index < len(self.model.state_history) - 1
        self.signals.history_changed.emit(can_undo, can_redo)

    def refresh_selection_history_status(self):
        """主动查询并发出当前筛选页历史的状态信号。"""
        self._emit_history_change()

    # --- 排序页方法 ---
    def initialize_sorting_data(self):
        """
        进入排序页时调用。
        1. 同步排序数据与第二页的勾选状态，移除已被取消勾选的条目。
        2. 如果同步导致数据变化，则重置排序历史。
        3. 确保高亮状态有效。
        """
        # 1. 同步数据
        original_final_sequence_len = len(self.model.final_sequence)
        all_selected_indices = {i for i, selected in enumerate(self.model.selection_state) if selected}
        
        self.model.final_sequence = [idx for idx in self.model.final_sequence if idx in all_selected_indices]
        self.model.final_selection.intersection_update(all_selected_indices)
        self.model.available_selection.intersection_update(all_selected_indices)
        
        data_changed = original_final_sequence_len != len(self.model.final_sequence)
        
        # 2. 校验并设置高亮
        if self.model.final_highlight not in self.model.final_sequence:
            self.model.final_highlight = self.model.final_sequence[0] if self.model.final_sequence else -1
            
        final_indices_set = set(self.model.final_sequence)
        available_indices = sorted(list(all_selected_indices - final_indices_set))
        if self.model.available_highlight not in available_indices:
            self.model.available_highlight = available_indices[0] if available_indices else -1
            
        # 3. 如果数据有变，重置历史记录
        if data_changed:
            self.model.reset_sorting_history()
            self._emit_sorting_history_change()

        # 发出信号，通知UI刷新
        self.signals.sorting_data_changed.emit()
        self.calculate_and_emit_sorting_statistics()

    def update_sorting_selection(self, list_name, indices_to_change, select_state):
        selection_set = self.model.available_selection if list_name == 'available' else self.model.final_selection
        if select_state:
            selection_set.update(indices_to_change)
        else:
            selection_set.difference_update(indices_to_change)
        # 不再记录历史
        self.signals.sorting_data_changed.emit()

    def set_sorting_highlight(self, list_name, original_index):
        if list_name == 'available':
            self.model.available_highlight = original_index
        else:
            self.model.final_highlight = original_index
        # 不再记录历史
        self.signals.sorting_data_changed.emit()

    def transfer_items_to_final(self, mode):
        if not self.model.available_selection: return
        
        items_to_move = sorted(list(self.model.available_selection))
        
        if mode == 'start':
            insert_pos = 0
        elif mode == 'end':
            insert_pos = len(self.model.final_sequence)
        else: # 'cursor'
            try:
                insert_pos = self.model.final_sequence.index(self.model.final_highlight) + 1
            except ValueError:
                insert_pos = len(self.model.final_sequence)

        self.model.final_sequence[insert_pos:insert_pos] = items_to_move
        
        all_indices = [i for i, s in enumerate(self.model.selection_state) if s]
        current_available = sorted(list(set(all_indices) - set(self.model.final_sequence)))
        
        try:
            old_highlight_pos = all_indices.index(self.model.available_highlight)
            next_indices = [i for i in all_indices[old_highlight_pos+1:] if i in current_available]
            if next_indices: self.model.available_highlight = next_indices[0]
            else:
                prev_indices = [i for i in all_indices[:old_highlight_pos] if i in current_available]
                self.model.available_highlight = prev_indices[-1] if prev_indices else -1
        except (ValueError, IndexError):
             self.model.available_highlight = current_available[0] if current_available else -1

        self.model.final_highlight = items_to_move[-1]
        self.model.available_selection.clear()
        self.model.final_selection = set(items_to_move)
        self.record_sorting_history_state()
        self.signals.sorting_data_changed.emit()
        self.calculate_and_emit_sorting_statistics()

    def return_items_from_final(self):
        if not self.model.final_selection: return
        
        items_to_return = self.model.final_selection.copy()
        
        try:
            old_highlight_pos = self.model.final_sequence.index(self.model.final_highlight)
            remaining_sequence = [i for i in self.model.final_sequence if i not in items_to_return]
            if old_highlight_pos < len(remaining_sequence):
                self.model.final_highlight = remaining_sequence[old_highlight_pos]
            else:
                self.model.final_highlight = remaining_sequence[-1] if remaining_sequence else -1
        except (ValueError, IndexError):
            self.model.final_highlight = -1

        self.model.final_sequence = [item for item in self.model.final_sequence if item not in items_to_return]
        
        returned_items_sorted = sorted(list(items_to_return))
        self.model.available_highlight = returned_items_sorted[-1]
        self.model.final_selection.clear()
        self.model.available_selection = items_to_return
        self.record_sorting_history_state()
        self.signals.sorting_data_changed.emit()
        self.calculate_and_emit_sorting_statistics()
    
    def clear_all_sorting_selections(self):
        """取消排序页所有列表中的选中项。"""
        if not self.model.available_selection and not self.model.final_selection:
            return
        self.model.available_selection.clear()
        self.model.final_selection.clear()
        # 不再记录历史
        self.signals.sorting_data_changed.emit()

    # --- 排序页历史记录方法 ---
    def record_sorting_history_state(self):
        current_state = (
            self.model.final_sequence.copy(),
            self.model.available_selection.copy(),
            self.model.final_selection.copy(),
            self.model.available_highlight,
            self.model.final_highlight
        )
        
        last_recorded_state = self.model.sorting_state_history[self.model.sorting_history_index]
        if current_state == last_recorded_state:
            return

        if self.model.sorting_history_index < len(self.model.sorting_state_history) - 1:
            self.model.sorting_state_history = self.model.sorting_state_history[:self.model.sorting_history_index + 1]

        self.model.sorting_state_history.append(current_state)
        self.model.sorting_history_index += 1

        if len(self.model.sorting_state_history) > self.model.MAX_HISTORY_SIZE:
            self.model.sorting_state_history.pop(0)
            self.model.sorting_history_index -= 1

        self._emit_sorting_history_change()

    def undo_sorting(self):
        if self.model.sorting_history_index > 0:
            self.model.sorting_history_index -= 1
            self._apply_sorting_history_state()
        else:
            MessageBoxes.show_message(self.main_window, "提示", "已是第一条记录。", "warning")

    def redo_sorting(self):
        if self.model.sorting_history_index < len(self.model.sorting_state_history) - 1:
            self.model.sorting_history_index += 1
            self._apply_sorting_history_state()
        else:
            MessageBoxes.show_message(self.main_window, "提示", "已是最后一条记录。", "warning")

    def _apply_sorting_history_state(self):
        (
            final_sequence,
            available_selection,
            final_selection,
            available_highlight,
            final_highlight
        ) = self.model.sorting_state_history[self.model.sorting_history_index]
        
        # BUG-FIX: 使用副本恢复状态，以防止对历史记录本身的意外修改
        self.model.final_sequence = final_sequence.copy()
        self.model.available_selection = available_selection.copy()
        self.model.final_selection = final_selection.copy()
        self.model.available_highlight = available_highlight
        self.model.final_highlight = final_highlight
        
        self.signals.sorting_data_changed.emit()
        self._emit_sorting_history_change()
        self.calculate_and_emit_sorting_statistics()

    def _emit_sorting_history_change(self):
        can_undo = self.model.sorting_history_index > 0
        can_redo = self.model.sorting_history_index < len(self.model.sorting_state_history) - 1
        self.signals.sorting_history_changed.emit(can_undo, can_redo)
        
    def refresh_sorting_history_status(self):
        """主动查询并发出当前排序历史的状态信号。"""
        self._emit_sorting_history_change()
        
    # --- 视频合成方法 ---
    def create_synthesis_worker(self, video_paths):
        return SynthesisWorker(self.model, video_paths)