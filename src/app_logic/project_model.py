# path: src/app_logic/project_model.py

# ◔ 说明: 项目数据模型，遵循MVC架构思想中的Model角色。
#          负责持有和管理当前活动项目的所有数据。

class ProjectModel:
    """
    一个简单的数据容器，用于存储当前加载项目的所有状态和数据。
    这确保了数据与UI和业务逻辑的分离。
    """
    def __init__(self):
        self.project_path = None
        self.video_meta = {}
        self.subtitle_data = []
        self.selection_state = []
        self.is_initialized = False

        # 关键词搜索状态
        self.search_query = ""
        self.search_results = []
        self.search_current_index = -1
        
        # 历史记录 (用于筛选页)
        self.state_history = []
        self.history_index = -1
        self.MAX_HISTORY_SIZE = 20

        # --- 排序页状态 ---
        # 存储原始索引 (int) 的列表，代表最终的句子顺序
        self.final_sequence = []
        # 分别存储两个列表中被选中项的原始索引 (set[int])
        self.available_selection = set()
        self.final_selection = set()
        # 分别存储两个列表中高亮项的原始索引 (int)
        self.available_highlight = -1
        self.final_highlight = -1
        # 排序页的历史记录
        self.sorting_state_history = []
        self.sorting_history_index = -1


    def load_data(self, video_meta, subtitle_data):
        """
        加载解析后的数据到模型中。
        此方法会完全覆盖旧数据, 并重置历史记录和排序状态为默认值。
        """
        print("--- ProjectModel: load_data ---") # 临时打印
        self.video_meta = video_meta
        self.subtitle_data = subtitle_data
        self.selection_state = [False] * len(subtitle_data)
        self.is_initialized = True
        self.reset_search_state()
        self.reset_sorting_state() # 重置排序状态
        
        # 重置历史记录并存入初始状态 (选择状态, 高亮索引)
        print("  正在将筛选页历史记录重置为默认的 '全未选' 状态...") # 临时打印
        initial_state = (self.selection_state.copy(), 0)
        self.state_history = [initial_state]
        self.history_index = 0
        
        print("--- 项目数据已加载到模型, 历史记录已重置为默认。---") # 临时打印

    def reset(self):
        """重置所有数据，回到未加载状态。"""
        self.project_path = None
        self.video_meta = {}
        self.subtitle_data = []
        self.selection_state = []
        self.is_initialized = False
        self.reset_search_state()
        self.reset_sorting_state() # 重置排序状态
        
        # 清空历史记录
        self.state_history = []
        self.history_index = -1
        
        print("项目模型已重置。")

    def set_project_path(self, path):
        """设置当前项目的路径。"""
        self.project_path = path
        
    def reset_search_state(self):
        """重置搜索状态。"""
        self.search_query = ""
        self.search_results = []
        self.search_current_index = -1

    def reset_sorting_state(self):
        """重置排序页的所有状态（包括历史记录）。"""
        self.final_sequence = []
        self.available_selection = set()
        self.final_selection = set()
        self.available_highlight = -1
        self.final_highlight = -1
        self.reset_sorting_history()

    def reset_sorting_history(self):
        """重置排序页的历史记录，并将当前状态作为初始快照。"""
        print("  [Model] 正在根据当前 final_sequence 重置排序页历史记录...") # 临时打印
        initial_state = (
            self.final_sequence.copy(),
            self.available_selection.copy(),
            self.final_selection.copy(),
            self.available_highlight,
            self.final_highlight
        )
        self.sorting_state_history = [initial_state]
        self.sorting_history_index = 0