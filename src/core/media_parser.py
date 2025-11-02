# path: src/core/media_parser.py

# 媒体解析器 - 统一入口模块

import os
from .srt_parser import SrtParser
from .video_parser import VideoParser

class MediaParser:
    """
    作为核心解析功能的总调度者。
    负责校验源文件目录、调用具体解析器并返回整合后的数据。
    """
    def __init__(self):
        self.srt_parser = SrtParser()
        self.video_parser = VideoParser()
        self.video_paths = []
        self.srt_path = None

    def validate_source_directory(self, source_dir_path):
        """
        校验源文件目录是否合法。
        合法标准：必须且只能包含一个 .srt 文件。视频文件为可选。
        """
        try:
            files = os.listdir(source_dir_path)
        except FileNotFoundError:
            return False, f"源目录不存在: {source_dir_path}"

        self.video_paths = [os.path.join(source_dir_path, f) for f in files if f.lower().endswith('.mp4')]
        srt_files = [f for f in files if f.lower().endswith('.srt')]

        if len(srt_files) == 0:
            return False, "源目录中未找到 SRT 字幕文件。"
        if len(srt_files) > 1:
            return False, "源目录中存在多个 SRT 文件，请确保只有一个。"

        self.srt_path = os.path.join(source_dir_path, srt_files[0])
        return True, "源目录校验通过。"

    def parse(self, source_dir_path):
        """
        执行解析。
        返回 (视频元数据字典, 字幕数据列表)。
        如果源目录中没有视频，则视频元数据字典为空。
        """
        is_valid, msg = self.validate_source_directory(source_dir_path)
        if not is_valid:
            raise ValueError(f"无法解析，源目录校验失败: {msg}")

        subtitle_data = self.srt_parser.parse(self.srt_path)
        
        video_meta = {}
        if self.video_paths:
            # 如果有视频，解析第一个作为代表性元数据
            video_meta = self.video_parser.parse(self.video_paths[0])

        return video_meta, subtitle_data