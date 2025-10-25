# path: src/core/video_processor.py

import os
import re
import sys
import subprocess
import time
import json
from datetime import datetime, timedelta
import openpyxl
from openpyxl.utils import get_column_letter
import copy

from utils.resource_path import get_resource_path
from core.srt_parser import SrtParser

class VideoProcessor:
    def __init__(self):
        try:
            # 【核心修改】根据操作系统构建完整的相对路径，再交给 get_resource_path 解析
            if sys.platform == "win32":
                ffmpeg_rel_path = "vendor/ffmpeg_win/ffmpeg.exe"
                ffprobe_rel_path = "vendor/ffmpeg_win/ffprobe.exe"
            else:  # macOS 或 Linux
                ffmpeg_rel_path = "vendor/ffmpeg_mac/ffmpeg"
                ffprobe_rel_path = "vendor/ffmpeg_mac/ffprobe"
            
            self.ffmpeg_path = get_resource_path(ffmpeg_rel_path)
            self.ffprobe_path = get_resource_path(ffprobe_rel_path)

        except FileNotFoundError as e:
            print(f"严重错误: 无法找到 ffmpeg/ffprobe: {e}")
            self.ffmpeg_path = None
            self.ffprobe_path = None
        
        self.srt_converter = SrtParser()

    def _load_clip_manifest(self, manifest_path):
        if os.path.exists(manifest_path):
            try:
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if not content:
                        return {}
                    return json.loads(content)
            except (json.JSONDecodeError, IOError) as e:
                print(f"警告: 加载或解析清单文件失败: {e}")
                return {}
        return {}

    def _save_clip_manifest(self, manifest_path, data):
        try:
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except IOError as e:
            print(f"错误: 写入清单文件失败: {e}")

    def _seconds_to_hmsm(self, seconds):
        td = timedelta(seconds=seconds)
        total_minutes, sec = divmod(td.seconds, 60)
        hrs, mins = divmod(total_minutes, 60)
        ms = td.microseconds // 1000
        return f"{hrs:02d}:{mins:02d}:{sec:02d}.{ms:03d}"

    def _seconds_to_hms(self, seconds):
        """将秒数格式化为 HH:MM:SS，不含毫秒。"""
        td = timedelta(seconds=seconds)
        total_minutes, sec = divmod(td.seconds, 60)
        hrs, mins = divmod(total_minutes, 60)
        return f"{hrs:02d}:{mins:02d}:{sec:02d}"

    def _seconds_to_filename_time(self, seconds):
        td = timedelta(seconds=seconds)
        minutes, sec = divmod(td.seconds, 60)
        hours, minutes = divmod(minutes, 60)
        milliseconds = td.microseconds // 1000
        return f"{hours:02d}{minutes:02d}{sec:02d}{milliseconds:03d}"

    def _normalize_filename(self, text):
        text = text.replace('\n', ' ').strip()
        safe_text = re.sub(r'[\\/*?:"<>|]', '', text)
        safe_text = re.sub(r'\s+', '_', safe_text)
        return safe_text[:50]

    def preprocess_srt_times(self, srt_data, video_duration):
        if not srt_data:
            return []
        processed_data = copy.deepcopy(srt_data)
        processed_data[0]['start_seconds'] = 0.0
        processed_data[-1]['end_seconds'] = video_duration

        for i in range(len(processed_data) - 1):
            current_sub = processed_data[i]
            next_sub = processed_data[i+1]
            gap = next_sub['start_seconds'] - current_sub['end_seconds']
            if gap > 0:
                midpoint_offset = gap / 2.0
                current_sub['end_seconds'] += midpoint_offset
                next_sub['start_seconds'] -= midpoint_offset

        for item in processed_data:
            item['start'] = self.srt_converter._seconds_to_time(item['start_seconds'])
            item['end'] = self.srt_converter._seconds_to_time(item['end_seconds'])
            item['duration'] = round(item['end_seconds'] - item['start_seconds'], 3)
        
        return processed_data

    def cut_and_save_clips(self, source_video_path, source_video_size, final_sequence_data, clips_dir, manifest_path):
        if not self.ffmpeg_path:
            raise RuntimeError("FFmpeg 未找到。")

        manifest_data = self._load_clip_manifest(manifest_path)
        clip_paths = []
        
        for item_data in final_sequence_data:
            start_sec = item_data['start_seconds']
            duration_sec = item_data['duration']
            
            start_time_fn = self._seconds_to_filename_time(start_sec)
            end_time_fn = self._seconds_to_filename_time(start_sec + duration_sec)
            normalized_text = self._normalize_filename(item_data['text'])
            
            clip_filename = f"{start_time_fn}_{end_time_fn}_{normalized_text}.mp4"
            clip_filepath = os.path.join(clips_dir, clip_filename)

            source_basename_for_comp = os.path.basename(source_video_path)
            source_size_for_comp = str(source_video_size)
            
            # 使用 JSON 清单进行校验
            if os.path.exists(clip_filepath):
                manifest_entry = manifest_data.get(clip_filename)
                if manifest_entry:
                    entry_name = manifest_entry.get('original_filename')
                    entry_size = str(manifest_entry.get('original_filesize'))
                    if entry_name == source_basename_for_comp and entry_size == source_size_for_comp:
                        clip_paths.append(clip_filepath)
                        continue
            
            # 构造 ffmpeg 命令
            command = [
                self.ffmpeg_path, '-ss', str(start_sec), '-i', source_video_path,
                '-t', str(duration_sec), '-map', '0', '-y', clip_filepath
            ]
            
            try:
                subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
                clip_paths.append(clip_filepath)
                # 更新清单字典
                manifest_data[clip_filename] = {
                    "original_filename": source_basename_for_comp,
                    "original_filesize": source_size_for_comp
                }
            except subprocess.CalledProcessError as e:
                print(f"错误: FFmpeg剪切片段失败: {clip_filename}\n{e.stderr}")
                continue

        self._save_clip_manifest(manifest_path, manifest_data)
        return clip_paths

    def concatenate_clips(self, clip_paths, output_path):
        if not self.ffmpeg_path:
            raise RuntimeError("FFmpeg 未找到。")
        if not clip_paths:
            raise ValueError("片段列表为空, 无法拼接。")

        list_filepath = os.path.join(os.path.dirname(output_path), "concat_list.txt")
        with open(list_filepath, 'w', encoding='utf-8') as f:
            for path in clip_paths:
                safe_path = path.replace("'", "'\\''")
                f.write(f"file '{safe_path}'\n")
        
        command = [
            self.ffmpeg_path, '-f', 'concat', '-safe', '0', '-i', list_filepath,
            '-c', 'copy', '-y', output_path
        ]

        try:
            subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"FFmpeg拼接视频失败: {e.stderr}")
        finally:
            if os.path.exists(list_filepath):
                os.remove(list_filepath)
        
    def create_mapping_excel(self, source_video_meta, final_sequence_data, original_sequence_data, excel_path, output_video_path, total_synthesis_duration):
        wb = openpyxl.Workbook()
        ws1 = wb.active
        ws1.title = "元数据"
        
        ws1.append(["原始视频信息", ""])
        ws1.append(["文件名", os.path.basename(source_video_meta.get('filename', 'N/A'))])
        ws1.append(["大小 (字节)", source_video_meta.get('size')])
        ws1.append(["时长 (秒)", source_video_meta.get('duration')])
        ws1.append(["尺寸", f"{source_video_meta.get('width')}x{source_video_meta.get('height')}"])
        ws1.append(["帧率", source_video_meta.get('frame_rate')])
        ws1.append(["视频编码", source_video_meta.get('codec_name')])
        ws1.append(["音频编码", source_video_meta.get('audio_codec_name')])
        ws1.append(["", ""])
        
        output_duration = 0
        try:
            probe_cmd = [self.ffprobe_path, '-v', 'quiet', '-print_format', 'json', '-show_format', output_video_path]
            result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True, encoding='utf-8', errors='ignore')
            output_meta = json.loads(result.stdout)
            output_duration = float(output_meta['format']['duration'])
        except Exception as e:
            print(f"警告: 无法获取输出视频时长: {e}")
            
        total_dialogue_duration = sum(item['duration'] for item in original_sequence_data)
        total_dialogue_chars = sum(len(item['text']) for item in original_sequence_data)
        
        ws1.append(["合成任务信息", ""])
        ws1.append(["输出文件名", os.path.basename(output_video_path)])
        ws1.append(["总耗时 (秒)", f"{total_synthesis_duration:.2f}"])
        ws1.append(["采用片段数", len(final_sequence_data)])
        ws1.append(["输出总时长 (秒)", output_duration])
        ws1.append(["有台词时长 (秒)", total_dialogue_duration])
        ws1.append(["台词总字数", total_dialogue_chars])

        segments = []
        cumulative_duration = 0.0
        for item in final_sequence_data:
            duration = item['duration']
            segments.append({
                'orig_start': item['start_seconds'], 'orig_end': item['end_seconds'],
                'out_start': cumulative_duration, 'duration': duration
            })
            cumulative_duration += duration
            
        ws2 = wb.create_sheet("原始->粗剪")
        ws2.append(["原始视频时间点 (秒)", "粗剪影片时间点 (HH:MM:SS.ms)"])
        source_duration_int = int(source_video_meta.get('duration', 0))
        for t_orig in range(source_duration_int + 1):
            mapped_time = "Null"
            for seg in segments:
                if seg['orig_start'] <= t_orig < seg['orig_end']:
                    t_out = seg['out_start'] + (t_orig - seg['orig_start'])
                    mapped_time = self._seconds_to_hmsm(t_out)
                    break
            ws2.append([self._seconds_to_hms(t_orig), mapped_time])

        ws3 = wb.create_sheet("粗剪->原始")
        ws3.append(["粗剪影片时间点 (秒)", "原始视频时间点 (HH:MM:SS.ms)"])
        output_duration_int = int(output_duration)
        for t_out in range(output_duration_int + 1):
            mapped_time = "Error"
            for seg_idx, seg in enumerate(segments):
                is_last_segment = (seg_idx == len(segments) - 1)
                if (seg['out_start'] <= t_out < (seg['out_start'] + seg['duration'])) or \
                   (is_last_segment and abs(t_out - (seg['out_start'] + seg['duration'])) < 0.001):
                    t_orig = seg['orig_start'] + (t_out - seg['out_start'])
                    t_orig = min(t_orig, seg['orig_end'])
                    mapped_time = self._seconds_to_hmsm(t_orig)
                    break
            ws3.append([self._seconds_to_hms(t_out), mapped_time])
            
        for ws in [ws1, ws2, ws3]:
            for col in ws.columns:
                max_length = 0
                column = col[0].column_letter
                for cell in col:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(cell.value)
                    except: pass
                adjusted_width = (max_length + 2)
                ws.column_dimensions[column].width = adjusted_width

        wb.save(excel_path)