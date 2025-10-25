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
            # 【核心修改】根据操作系统构建完整的相对路径，再交给 get_resource_path 解析
            if sys.platform == "win32":
                ffprobe_rel_path = "vendor/ffmpeg_win/ffprobe.exe"
            else:  # macOS 或 Linux
                ffprobe_rel_path = "vendor/ffmpeg_mac/ffprobe"
            
            self.ffprobe_path = get_resource_path(ffprobe_rel_path)

        except FileNotFoundError as e:
            print(f"严重错误: {e}")
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

            # 从分数格式（如 "24000/1001"）计算帧率
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
            print(f"错误: 使用 ffprobe 解析视频失败: {e}")
            return {}

# --- 测试代码 ---
if __name__ == '__main__':
    # 注意: 此测试需要一个有效的视频文件 'test.mp4' 和 ffprobe 在 vendor 目录中。
    # 创建一个假的 test.mp4 文件用于路径测试
    with open("test.mp4", "w") as f:
        f.write("dummy video file")
        
    parser = VideoParser()
    # 正常情况下会失败，因为文件无效，但可以测试命令是否能构建
    print(f"FFprobe 路径: {parser.ffprobe_path}")
    metadata = parser.parse("test.mp4")
    print(metadata)
    
    import os
    os.remove("test.mp4")