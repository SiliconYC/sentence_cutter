# path: src/app_logic/project_controller.py

# ◔ 说明: 项目控制器，遵循MVC架构思想中的Controller角色。
#          负责处理项目新建、加载、保存、重置等核心业务逻辑。

import os
import json
from PySide6.QtWidgets import QFileDialog

from core.media_parser import MediaParser
from ui.dialogs.new_project_dialog import NewProjectDialog
from ui.widgets.message_dialogs import MessageBoxes
from utils.config_manager import ConfigManager
from utils.app_config import CONFIG_FILENAME, PROJECT_SUBDIRS, SOURCE_DIR_NAME, INTERMEDIATE_DIR_NAME

class ProjectController:
    """
    该类封装了所有与项目生命周期相关的操作，
    使主窗口(View)的逻辑保持简洁。
    """
    def __init__(self, main_window, model):
        self.main_window = main_window
        self.model = model
        self.config_manager = ConfigManager(CONFIG_FILENAME)
        self.state_filename = "project_state.json"
        self.meta_filename = "video_meta.json"
        self.srt_data_filename = "subtitle_data.json"

    def new_project(self):
        """处理新建项目流程。"""
        config = self.config_manager.load_config()
        last_root = config.get("last_project_root_dir", "")

        dialog = NewProjectDialog(self.main_window, last_root_dir=last_root)
        if dialog.exec():
            project_info = dialog.get_project_info()
            root_dir = project_info["root_dir"]
            project_name = project_info["project_name"]
            
            self.config_manager.update_config({"last_project_root_dir": root_dir})

            new_project_path = os.path.join(root_dir, project_name)
            if self._create_project_structure(new_project_path):
                self.load_project(new_project_path)

    def load_project(self, path=None):
        """处理加载项目流程。如果未提供路径，则弹出对话框。"""
        # 自动保存当前项目
        if self.model.project_path:
            self.save_project(show_notification=False)

        if not path:
            config = self.config_manager.load_config()
            last_root = config.get("last_project_root_dir", "")
            path = QFileDialog.getExistingDirectory(self.main_window, "请选择项目目录", last_root)
        
        if path and self._is_valid_project(path):
            print("\n\n[开始] ProjectController: load_project")
            print(f"[信息] 项目路径: {path}")
            self.model.reset() # 清理旧模型数据
            self.model.set_project_path(path)

            # 步骤 1: 尝试从 intermediate 加载已解析的数据
            print("[步骤 1/3] 正在尝试从 02_Intermediate 加载已解析数据...")
            intermediate_dir = os.path.join(path, INTERMEDIATE_DIR_NAME)
            meta_path = os.path.join(intermediate_dir, self.meta_filename)
            srt_data_path = os.path.join(intermediate_dir, self.srt_data_filename)

            if os.path.exists(meta_path) and os.path.exists(srt_data_path):
                try:
                    with open(meta_path, 'r', encoding='utf-8') as f:
                        video_meta = json.load(f)
                    with open(srt_data_path, 'r', encoding='utf-8') as f:
                        subtitle_data = json.load(f)
                    
                    self.model.load_data(video_meta, subtitle_data)
                    print("[信息] 已解析数据加载成功, 模型已初始化。")
                    print(f"[状态] is_initialized 状态: {self.model.is_initialized}")

                    # 步骤 2: 加载用户的编辑状态
                    print("[步骤 2/3] 正在加载用户编辑状态...")
                    self._load_project_state()

                except Exception as e:
                    print(f"[警告] 加载已解析数据失败: {e}。项目将处于未初始化状态。")
            else:
                print("[信息] 未找到已解析的数据文件。项目将处于未初始化状态, 等待用户手动初始化。")

            # 步骤 3: 更新全局配置并显示UI
            print("[步骤 3/3] 更新全局配置并显示编辑器...")
            config = self.config_manager.load_config()
            recent_projects = config.get("recent_projects", [])
            if path in recent_projects:
                recent_projects.remove(path)
            recent_projects.insert(0, path)
            self.config_manager.update_config({
                "last_project_root_dir": os.path.dirname(path),
                "recent_projects": recent_projects[:10]
            })
            
            print(f"[完成] 项目成功加载: {path}")
            self.main_window.show_editor_view()
        elif path:
            MessageBoxes.show_message(self.main_window, "加载失败", f"无效的项目目录：\n{path}", "warning")

    def save_project(self, show_notification=True):
        """保存当前项目的状态。"""
        if not self.model.project_path or not self.model.is_initialized:
            if show_notification:
                MessageBoxes.show_message(self.main_window, "无法保存", "当前没有加载或初始化任何项目。", "info")
            return
        
        state_path = os.path.join(self.model.project_path, INTERMEDIATE_DIR_NAME, self.state_filename)
        
        data_to_save = {
            "selection_state": self.model.selection_state,
            "final_sequence": self.model.final_sequence
        }

        try:
            with open(state_path, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, indent=4)
            
            print(f"[信息] 项目状态已保存至: {state_path}")
            if show_notification:
                MessageBoxes.show_message(self.main_window, "保存成功", "当前项目的编辑状态已保存。", "success")
        except Exception as e:
            print(f"[错误] 保存项目状态失败: {e}")
            if show_notification:
                 MessageBoxes.show_message(self.main_window, "保存失败", f"无法保存项目状态:\n{e}", "warning")

    def _load_project_state(self):
        """(私有) 尝试从文件加载项目状态到模型, 并执行严格校验。"""
        state_path = os.path.join(self.model.project_path, INTERMEDIATE_DIR_NAME, self.state_filename)
        print(f"[信息] 正在检查状态文件: {state_path}")
        
        if not os.path.exists(state_path):
            print("[信息] 项目状态文件不存在, 将使用默认编辑状态。")
            return

        try:
            with open(state_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print("[信息] 状态文件找到并成功读取。正在校验数据...")
            
            selection_state = data.get("selection_state")
            final_sequence = data.get("final_sequence")
            
            # --- 开始严格校验 ---
            num_subtitles = len(self.model.subtitle_data)
            is_valid = True
            
            # 校验1: selection_state 格式和长度
            if not isinstance(selection_state, list) or len(selection_state) != num_subtitles:
                print(f"[校验失败] 'selection_state' 格式或长度不匹配 (文件: {len(selection_state) if isinstance(selection_state, list) else 'N/A'}, 当前: {num_subtitles})。")
                is_valid = False
            
            # 校验2: final_sequence 格式及内容
            if is_valid and isinstance(final_sequence, list):
                for index in final_sequence:
                    if not (isinstance(index, int) and 0 <= index < num_subtitles and selection_state[index] is True):
                        print(f"[校验失败] 'final_sequence' 包含无效或未选中的索引: {index}。")
                        is_valid = False
                        break
            elif not isinstance(final_sequence, list):
                 print(f"[校验失败] 'final_sequence' 不是列表。")
                 is_valid = False

            # --- 校验结束 ---
            
            if is_valid:
                self.model.selection_state = selection_state
                self.model.final_sequence = final_sequence
                print("[信息] 校验成功, 已恢复已保存的编辑状态。")
                
                # 【BUG修复】将加载的状态设置为历史记录的基线
                print("[信息] 正在将加载的状态设置为历史记录的第一条...")
                initial_state = (self.model.selection_state.copy(), 0)
                self.model.state_history = [initial_state]
                self.model.history_index = 0
                self.model.reset_sorting_history()
                print("[信息] 历史记录基线设置完毕。")
                
            else:
                print("[警告] 状态文件数据无效, 将其删除并使用默认编辑状态。")
                del selection_state
                del final_sequence
                os.remove(state_path)

        except Exception as e:
            print(f"[警告] 加载或校验项目状态文件时出错: {e}。将删除文件并使用默认状态。")
            if os.path.exists(state_path):
                os.remove(state_path)


    def reset_project(self):
        """重置当前项目，返回欢迎界面。"""
        self.save_project(show_notification=False)
        confirmed = MessageBoxes.ask_confirmation(
            self.main_window, "确认关闭项目", "您确定要关闭当前项目吗？\n所有编辑进度都已自动保存。"
        )
        if confirmed:
            self.model.reset()
            self.main_window.show_welcome_view()

    def _create_project_structure(self, project_path):
        if os.path.exists(project_path):
            MessageBoxes.show_message(self.main_window, "创建失败", f"项目目录已存在：\n{project_path}", "warning")
            return False
        try:
            os.makedirs(project_path)
            for subdir in PROJECT_SUBDIRS:
                os.makedirs(os.path.join(project_path, subdir))
            
            MessageBoxes.show_message(
                self.main_window, "项目创建成功", 
                f"项目 '{os.path.basename(project_path)}' 已创建。\n\n请将您的SRT文件放入 '{SOURCE_DIR_NAME}' 文件夹中。", "success"
            )
            return True
        except Exception as e:
            MessageBoxes.show_message(self.main_window, "创建失败", f"创建项目目录时发生错误：\n{e}", "warning")
            return False

    def _is_valid_project(self, path):
        return os.path.isdir(os.path.join(path, SOURCE_DIR_NAME))