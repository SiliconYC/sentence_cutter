# path: src/ui/widgets/message_dialogs.py

# ◔ 说明: 从通用组件库迁移而来。按照行业实践，将原有的函数式弹窗封装为更标准的静态方法类。
#          提供了信息、警告、成功、确认等多种常用对话框。

import sys
from PySide6.QtWidgets import (
    QMessageBox, QApplication, QCheckBox, QMainWindow
)
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import Qt, QTimer, QObject, QEvent

# 【核心修改 1】 导入工具
from utils.resource_path import get_resource_path

class MessageBoxes:
    """
    提供一组静态方法来显示标准化的消息对话框。
    这比直接使用QMessageBox更方便，并确保了UI风格的统一。
    """
    
    # 路径现在是相对项目根目录的
    ICON_PATHS = {
        "warning": "assets/icons/dialogs/warning.png",
        "info": "assets/icons/dialogs/info.png",
        "success": "assets/icons/dialogs/success.png",
        "question": "assets/icons/dialogs/question.png"
    }

    @staticmethod
    def _create_base_dialog(parent, title, text, icon_type):
        """创建一个基础的QMessageBox实例并进行通用设置。"""
        dialog = QMessageBox(parent)
        dialog.setWindowTitle(title)
        dialog.setText(text)

        if parent and parent.windowIcon():
            dialog.setWindowIcon(parent.windowIcon())
        
        relative_icon_path = MessageBoxes.ICON_PATHS.get(icon_type)
        if relative_icon_path:
            # 【核心修改 2】 使用 get_resource_path 获取图标的绝对路径
            try:
                absolute_icon_path = get_resource_path(relative_icon_path)
                pixmap = QPixmap(absolute_icon_path).scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                dialog.setIconPixmap(pixmap)
            except FileNotFoundError as e:
                print(f"警告: 消息框图标未找到: {e}")
        
        for button in dialog.buttons():
            button.setCursor(Qt.CursorShape.PointingHandCursor)

        return dialog

    @staticmethod
    def show_message(parent, title, text, msg_type="info", duration=None):
        """
        显示一个单向通知消息（如信息、成功、警告）。
        
        Args:
            parent: 父控件。
            title (str): 对话框标题。
            text (str): 对话框正文。
            msg_type (str): 消息类型, 可选 "info", "success", "warning"。
            duration (int, optional): 自动关闭的秒数。用户点击可中断计时。
        """
        dialog = MessageBoxes._create_base_dialog(parent, title, text, msg_type)
        dialog.setStandardButtons(QMessageBox.StandardButton.Ok)

        if duration:
            timer = QTimer()
            timer.setSingleShot(True)
            timer.timeout.connect(dialog.close)
            timer.start(duration * 1000)
            
            # 安装事件过滤器，监听点击事件以停止计时器
            class ClickInterceptor(QObject):
                def eventFilter(self, watched, event):
                    if event.type() == QEvent.Type.MouseButtonPress:
                        timer.stop()
                        watched.removeEventFilter(self)
                    return super().eventFilter(watched, event)

            interceptor = ClickInterceptor()
            dialog.installEventFilter(interceptor)

        dialog.exec()
        
    @staticmethod
    def ask_confirmation(parent, title, text, confirm_text="确认", cancel_text="取消"):
        """
        显示一个双向确认对话框。
        
        Returns:
            bool: 如果用户点击确认按钮则返回 True, 否则返回 False。
        """
        dialog = MessageBoxes._create_base_dialog(parent, title, text, "question")
        confirm_button = dialog.addButton(confirm_text, QMessageBox.ButtonRole.AcceptRole)
        dialog.addButton(cancel_text, QMessageBox.ButtonRole.RejectRole)
        
        dialog.exec()
        
        return dialog.clickedButton() == confirm_button

    @staticmethod
    def show_placeholder(parent):
        """显示一个开发占位功能的快捷提示。"""
        MessageBoxes.show_message(
            parent,
            "开发中...",
            "该功能尚未完成，敬请期待！",
            msg_type="info"
        )


# ------------------- 测试代码 -------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = QMainWindow()
    main_window.setWindowTitle("MessageBoxes Test")
    
    # 请确保在项目根目录的 assets/icons/dialogs/ 路径下有名为
    # warning.png, info.png, success.png, question.png 的图标文件。
    
    print("测试1: 显示信息弹窗 (3秒后自动关闭)")
    MessageBoxes.show_message(main_window, "提示", "这是一条普通信息。", "info", duration=3)
    
    print("测试2: 显示成功弹窗")
    MessageBoxes.show_message(main_window, "成功", "操作已成功完成！", "success")

    print("测试3: 显示警告弹窗")
    MessageBoxes.show_message(main_window, "警告", "发生了一个需要注意的问题。", "warning")

    print("测试4: 显示确认对话框")
    confirmed = MessageBoxes.ask_confirmation(main_window, "请确认", "您确定要执行此操作吗？")
    print(f"用户的选择是: {'确认' if confirmed else '取消'}")

    print("测试5: 显示占位弹窗")
    MessageBoxes.show_placeholder(main_window)
    
    sys.exit()