# path: src/app_logic/__init__.py

# 该文件使得 app_logic 目录可以被 Python 解释器识别为一个子包。
# app_logic 包用于存放应用的核心业务逻辑和控制器代码，实现与UI的分离。

# 引入模型和控制器，方便上层调用
from .project_model import ProjectModel
from .project_controller import ProjectController
from .editor_controller import EditorController