# path: src/utils/config_manager.py

# 配置文件管理器
#
# 功能职责:
# 1. 负责应用程序配置的持久化存储，使用 JSON 格式。
# 2. 自动定位一个适合存放配置文件的用户目录（如 AppData 或 .config），以避免权限问题。
# 3. 提供加载配置文件的函数 (load_config)，在程序启动时调用。
# 4. 提供更新配置文件的函数 (update_config)，在配置项发生变化时调用。
# 5. 管理的配置项可能包括：上次使用的项目根目录、最近打开的项目列表等。

import os
import sys
import json
from pathlib import Path

class ConfigManager:
    """
    管理应用的配置文件，实现跨平台的持久化存储。
    """
    def __init__(self, filename="config.json"):
        """
        初始化配置管理器，并确定配置文件的最终路径。
        """
        config_dir = self._get_config_dir()
        self.config_path = config_dir / filename
        self._ensure_config_path_exists()

    def _get_config_dir(self) -> Path:
        """
        获取跨平台的应用配置目录路径。
        - Windows: C:/Users/<User>/AppData/Roaming/sentence_cutter
        - macOS: /Users/<User>/Library/Application Support/sentence_cutter
        - Linux: /home/<User>/.config/sentence_cutter
        """
        app_name = "sentence_cutter"
        
        if sys.platform == "win32":
            # APPDATA 是一个环境变量
            base_dir = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming"))
        elif sys.platform == "darwin": # macOS
            base_dir = Path.home() / "Library" / "Application Support"
        else: # Linux and other Unix-like
            # XDG_CONFIG_HOME 是标准, 降级方案是 ~/.config
            base_dir = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config"))
            
        return base_dir / app_name

    def _ensure_config_path_exists(self):
        """如果配置目录不存在，则创建它。"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

    def load_config(self) -> dict:
        """
        加载配置文件。如果文件不存在或内容为空/无效，则返回一个空字典。
        """
        if not self.config_path.exists():
            return {}
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if not content:
                    return {}
                return json.loads(content)
        except (json.JSONDecodeError, IOError) as e:
            print(f"[警告] 无法加载或解析配置文件 '{self.config_path}': {e}")
            return {}

    def update_config(self, new_data: dict):
        """
        更新配置文件。它会先加载现有配置，然后用新数据覆盖或添加键值。
        
        Args:
            new_data (dict): 一个包含要更新或添加的键值对的字典。
        """
        current_config = self.load_config()
        current_config.update(new_data)
        
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(current_config, f, indent=4, ensure_ascii=False)
        except IOError as e:
            print(f"[错误] 无法写入配置文件 '{self.config_path}': {e}")


# ------------------- 测试代码 -------------------
if __name__ == "__main__":
    print("--- 配置管理器测试 ---")
    
    # 1. 初始化，会自动创建目录
    # 注意：这里的 'test_config.json' 是为了避免覆盖真实配置
    test_manager = ConfigManager(filename="test_config.json") 
    print(f"配置文件路径: {test_manager.config_path}")
    print(f"路径是否存在: {test_manager.config_path.parent.exists()}")

    # 2. 初始加载 (文件应该还不存在)
    print("\n[测试] 初始加载...")
    config = test_manager.load_config()
    print(f"加载到的初始配置: {config}")
    assert config == {}

    # 3. 更新配置
    print("\n[测试] 更新配置...")
    test_manager.update_config({
        "last_project_root_dir": "D:/Projects",
        "theme": "dark_teal.xml"
    })
    print("已写入: {'last_project_root_dir': 'D:/Projects', 'theme': 'dark_teal.xml'}")

    # 4. 再次加载以验证
    config = test_manager.load_config()
    print(f"再次加载的配置: {config}")
    assert config["last_project_root_dir"] == "D:/Projects"

    # 5. 更新部分配置
    print("\n[测试] 更新部分配置...")
    test_manager.update_config({
        "theme": "light_blue.xml",
        "recent_projects": ["D:/Projects/Project_A"]
    })
    print("已写入: {'theme': 'light_blue.xml', 'recent_projects': ['D:/Projects/Project_A']}")

    # 6. 再次加载以验证合并效果
    config = test_manager.load_config()
    print(f"最终加载的配置: {config}")
    assert config["last_project_root_dir"] == "D:/Projects"
    assert config["theme"] == "light_blue.xml"
    assert len(config["recent_projects"]) == 1
    
    # 7. 清理测试文件
    if test_manager.config_path.exists():
        os.remove(test_manager.config_path)
        print(f"\n测试文件 '{test_manager.config_path}' 已删除。")

    print("\n--- 测试完成 ---")