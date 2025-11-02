# path: src/core/video_parser.py

# 视频元数据解析器

import sys
import json
import subprocess
from utils.resource_path import get_resource_path

class VideoParser:
    """
    依赖外部工具 ffprobe 来获取视频文件的详细信息。
    """
    def __init__(self):
        try:
            if sys.platform == "win32":
                ffprobe_rel_path = "vendor/ffmpeg_win/ffprobe.exe"
            else:  # macOS 或 Linux
                ffprobe_rel_path = "vendor/ffmpeg_mac/ffprobe"
            
            self.ffprobe_path = get_resource_path(ffprobe_rel_path)

        except FileNotFoundError as e:
            print(f"[严重错误] {e}")
            self.ffprobe_path = None

    def parse(self, video_path):
        """
        使用 ffprobe 获取视频元数据。
        返回包含关键信息的字典，如果失败则返回空字典。
        """
        if not self.ffprobe_path:
            raise RuntimeError("ffprobe 可执行文件未找到，无法解析视频。")

        command = [
            self.ffprobe_path,
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            video_path
        ]

        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8')
            data = json.loads(result.stdout)
            
            video_stream = next((s for s in data['streams'] if s['codec_type'] == 'video'), None)
            audio_stream = next((s for s in data['streams'] if s['codec_type'] == 'audio'), None)

            if not video_stream:
                return {}

            frame_rate_str = video_stream.get('r_frame_rate', '0/1')
            num, den = map(int, frame_rate_str.split('/'))
            frame_rate = round(num / den, 2) if den else 0

            return {
                'filename': data['format']['filename'],
                'duration': float(data['format']['duration']),
                'size': int(data['format']['size']),
                'width': video_stream.get('width'),
                'height': video_stream.get('height'),
                'codec_name': video_stream.get('codec_name'),
                'frame_rate': frame_rate,
                'audio_codec_name': audio_stream.get('codec_name') if audio_stream else None
            }

        except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError) as e:
            print(f"[错误] 使用 ffprobe 解析视频失败: {e}")
            return {}

    def get_video_duration(self, video_path: str) -> float:
        """
        快速获取视频时长，不解析其他元数据。
        """
        if not self.ffprobe_path:
            raise RuntimeError("ffprobe 可执行文件未找到，无法获取视频时长。")

        command = [
            self.ffprobe_path,
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            video_path
        ]
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8')
            return float(result.stdout.strip())
        except (subprocess.CalledProcessError, ValueError, FileNotFoundError) as e:
            print(f"[错误] 使用 ffprobe 获取视频时长失败: {e}")
            return 0.0