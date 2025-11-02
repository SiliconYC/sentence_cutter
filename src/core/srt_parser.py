# path: src/core/srt_parser.py

# SRT 字幕文件解析器

import re
from datetime import timedelta

class SrtParser:
    """
    负责读取和解析 .srt 字幕文件。
    """
    def _time_to_seconds(self, time_str):
        """将SRT时间格式 'HH:MM:SS,ms' 转换为总秒数。"""
        parts = re.split('[:,]', time_str)
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2]) + int(parts[3]) / 1000.0
    
    def _seconds_to_time(self, total_seconds):
        """将总秒数转换回SRT时间格式 'HH:MM:SS,ms'。"""
        if total_seconds < 0: total_seconds = 0
        td = timedelta(seconds=total_seconds)
        minutes, seconds = divmod(td.seconds, 60)
        hours, minutes = divmod(minutes, 60)
        milliseconds = td.microseconds // 1000
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

    def parse(self, file_path):
        """
        解析SRT文件。
        返回: 列表，每个元素是一个包含 'index', 'start', 'end', 'text', 'duration' 的字典。
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        subtitle_blocks = content.strip().split('\n\n')
        subtitles = []

        for block in subtitle_blocks:
            lines = block.split('\n')
            if len(lines) < 3:
                continue

            try:
                index = int(lines[0])
                time_line = lines[1]
                text = "\n".join(lines[2:])
                
                start_str, end_str = [t.strip() for t in time_line.split('-->')]
                
                start_sec = self._time_to_seconds(start_str)
                end_sec = self._time_to_seconds(end_str)
                duration = round(end_sec - start_sec, 3)

                subtitles.append({
                    'index': index,
                    'start': start_str,
                    'end': end_str,
                    'start_seconds': start_sec,
                    'end_seconds': end_sec,
                    'duration': duration,
                    'text': text
                })
            except (ValueError, IndexError) as e:
                print(f"警告：解析SRT块时跳过一个格式错误的块: {e}\n块内容: {block}")
                continue

        return subtitles