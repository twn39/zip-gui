import os
import sys


def resource_path(relative_path):
    """获取资源的绝对路径，适用于开发环境和 PyInstaller 打包环境"""
    try:
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def load_stylesheet(filename="theme.qss"):
    filepath = resource_path(filename)
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"加载样式文件时出错: {e}")
        return None
