# path: src/ui/widgets/markdown_viewer.py

# ◔ 说明: 从通用组件库 marki.py 移植并重构。
#          用于在窗口中渲染和显示Markdown文件内容。

from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextBrowser, QDialogButtonBox
from PySide6.QtCore import Qt
import markdown
from utils.resource_path import get_resource_path

class MarkdownViewer(QDialog):
    """一个用于显示Markdown内容的模态对话框。"""
    
    def __init__(self, parent, title, markdown_path=None, markdown_text=None):
        super().__init__(parent)
        
        if not markdown_path and not markdown_text:
            raise ValueError("必须提供 markdown_path 或 markdown_text。")

        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(800, 600)
        self.setStyleSheet("background-color: #FEF6E9;")

        self.text_browser = QTextBrowser()
        self.text_browser.setOpenExternalLinks(True)
        self.text_browser.setStyleSheet("border: none;")
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.addWidget(self.text_browser)
        layout.addWidget(buttons)

        self._load_content(markdown_path, markdown_text)

    def _load_content(self, path, text):
        """加载并渲染Markdown内容。"""
        if path:
            try:
                # 【核心修改】使用 get_resource_path 将相对路径转为绝对路径
                absolute_path = get_resource_path(path)
                with open(absolute_path, 'r', encoding='utf-8') as f:
                    md_text = f.read()
            except FileNotFoundError as e:
                md_text = f"# 错误\n\n无法找到文件: `{path}`\n\n详情: {e}"
        else:
            md_text = text

        html = markdown.markdown(md_text, extensions=['fenced_code', 'tables'])
        styled_html = self._apply_style(html)
        self.text_browser.setHtml(styled_html)

    def _apply_style(self, html):
        """为HTML内容应用CSS样式。"""
        style = """
        <style>
            body {
                background-color: #FEF6E9; color: #333333;
                font-family: Georgia, 'Times New Roman', serif;
                font-size: 16px; line-height: 1.7;
            }
            p, div, li, td, th, blockquote { color: #333333; }
            h1, h2, h3, h4, h5, h6 {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", Arial, sans-serif;
                color: #222222; border-bottom: 1px solid #ddd;
                padding-bottom: 8px; margin-top: 24px; margin-bottom: 16px;
            }
            h1 { font-size: 2.2em; } h2 { font-size: 1.8em; } h3 { font-size: 1.4em; }
            ul, ol { padding-left: 30px; color: #333333; }
            code {
                background-color: #E6DFD4; color: #3E3E3E;
                padding: 3px 6px; border-radius: 4px;
                font-family: Consolas, 'Courier New', monospace; font-size: 0.95em;
            }
            pre {
                background-color: #E6DFD4; padding: 1em;
                border-radius: 5px; overflow-x: auto;
            }
            pre code { padding: 0; background-color: transparent; border-radius: 0; }
            a { color: #0066cc; text-decoration: none; }
            a:hover { text-decoration: underline; }
        </style>
        """
        return f"{style}{html}"