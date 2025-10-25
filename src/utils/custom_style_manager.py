# path: src/utils/custom_style_manager.py

# ◔ 说明: 仿照 styli.py 的思路，创建一个配合 qt-material 使用的自定义样式管理器。
#          核心思想是在应用 qt-material 的基础上，追加或覆盖自定义的 QSS 规则。

import re
from qt_material import build_stylesheet

class CustomStyleManager:
    """
    加载 qt-material 的基础主题，并附加自定义的 QSS 样式，
    以实现对特定控件的精细化美化。
    """
    def __init__(self, app):
        """
        Args:
            app: QApplication 实例。
        """
        self.app = app
        self.base_theme = 'dark_teal.xml'

    def apply_style(self):
        """
        构建并应用最终的样式表。
        """
        # 1. 获取 qt-material 的基础样式表
        base_stylesheet = build_stylesheet(self.base_theme)

        # 2. (可选) 清理基础样式中我们不想要的部分，例如全局字体
        #    这可以确保我们自定义的字体能生效
        cleaned_stylesheet = self._strip_fonts(base_stylesheet)
        
        # 3. 定义我们自己的 QSS 规则
        custom_qss = self._get_custom_qss()

        # 4. 合并样式表并应用到整个程序
        final_stylesheet = cleaned_stylesheet + custom_qss
        self.app.setStyleSheet(final_stylesheet)

    def _strip_fonts(self, stylesheet):
        """
        使用正则表达式移除样式表中所有的 'font-family', 'font-size' 等属性。
        这可以防止基础主题的字体设置覆盖我们自己的定义。
        """
        # 匹配 font-family, font-size, font-weight, font-style 等
        font_regex = r"font-(family|size|weight|style|stretch|variant):[^;]+;"
        return re.sub(font_regex, "", stylesheet, flags=re.IGNORECASE)

    def _get_custom_qss(self):
        """
        返回包含所有自定义UI美化规则的QSS字符串。
        """
        return """
        /* --- WelcomeView --- */
        QLabel#welcomeLabel {
            font-family: Arial, 'Helvetica Neue', sans-serif; /* 改为无衬线字体 */
            font-size: 28px;
            color: #ecf0f1;
        }

        QPushButton#welcomeButton {
            font-family: Arial, 'Helvetica Neue', sans-serif;
            font-size: 22px;
            font-weight: bold;
        }

        /* --- Global --- */
        /* 可以添加其他全局样式, 例如 */
        QToolTip {
            border: 1px solid #76797C;
            padding: 5px;
            color: #eff0f1;
            background-color: #2b2b2b;
        }
        """