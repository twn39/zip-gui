# -*- coding: utf-8 -*-

import sys
import os
import shutil
import time # 用于模拟耗时操作（可选）

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox,
    QProgressBar, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal, QSize
from PySide6.QtGui import QIcon

# --- 直接导入 qtawesome，不再检查 ---
import qtawesome as qta

# --- 后台工作线程 (与之前相同) ---
class PackWorker(QThread):
    """
    执行打包任务的后台线程，避免阻塞 GUI。
    """
    # 定义信号
    finished = Signal(str)  # 任务完成信号，返回成功信息或空字符串
    error = Signal(str)     # 任务出错信号，返回错误信息
    progress = Signal(int)  # 进度信号 (0-100)

    def __init__(self, source_dir, dest_file_base, archive_format, root_dir):
        super().__init__()
        self.source_dir = source_dir
        self.dest_file_base = dest_file_base
        self.archive_format = archive_format
        self.root_dir = root_dir

    def run(self):
        """
        线程执行的入口点
        """
        try:
            self.progress.emit(10)
            print(f"开始打包: base_name='{self.dest_file_base}', format='{self.archive_format}', root_dir='{self.root_dir}'")

            archive_path = shutil.make_archive(
                base_name=self.dest_file_base,
                format=self.archive_format,
                root_dir=self.root_dir
            )

            # time.sleep(2) # 模拟耗时

            self.progress.emit(100)
            self.finished.emit(f"成功打包到: {archive_path}")

        except Exception as e:
            print(f"打包出错: {e}")
            self.error.emit(f"打包失败: {str(e)}")
        finally:
            pass

# --- 主窗口类 ---
class PackApp(QWidget):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.initUI() # initUI 现在可以安全地假设 qta 存在

    def initUI(self):
        self.setWindowTitle("简易文件夹打包工具 (黑色磨砂主题)")
        self.setGeometry(300, 300, 450, 400)

        # --- 布局 ---
        main_layout = QVBoxLayout()
        h_layout1 = QHBoxLayout()
        h_layout2 = QHBoxLayout()
        h_layout3 = QHBoxLayout()

        # --- 定义 qtawesome 图标属性 ---
        icon_size = QSize(20, 20)
        icon_color = "#A9A9A9"
        icon_color_active = "#E0E0E0"

        # --- 直接加载图标 (仍然保留 try-except 以防图标名称错误等问题) ---
        try:
            folder_icon = qta.icon('fa5s.folder-open', color=icon_color, color_active=icon_color_active)
            save_icon = qta.icon('fa5s.save', color=icon_color, color_active=icon_color_active)
            pack_icon = qta.icon('fa5s.compress-alt', color=icon_color, color_active=icon_color_active)
        except Exception as e:
            print(f"警告: 加载 qtawesome 图标时出错: {e}. 某些图标可能无法显示。")
            # 如果加载失败，则创建空图标，避免后续 setIcon 报错
            folder_icon = QIcon()
            save_icon = QIcon()
            pack_icon = QIcon()


        # --- 控件 ---
        # 1. 源文件夹
        self.source_label = QLabel("源文件夹:")
        self.source_edit = QLineEdit()
        self.source_edit.setPlaceholderText("请选择要打包的文件夹")
        self.source_button = QPushButton() # 移除文本
        self.source_button.setIcon(folder_icon) # 直接设置图标
        self.source_button.setIconSize(icon_size)
        self.source_button.setToolTip("选择源文件夹")

        h_layout1.addWidget(self.source_label)
        h_layout1.addWidget(self.source_edit)
        h_layout1.addWidget(self.source_button)

        # 2. 压缩类型
        self.format_label = QLabel("压缩类型:")
        self.format_combo = QComboBox()
        try:
            supported_formats = [fmt[0] for fmt in shutil.get_archive_formats()]
            self.format_combo.addItems(supported_formats)
        except Exception:
            self.format_combo.addItems(['zip', 'tar', 'gztar', 'bztar', 'xztar'])

        h_layout2.addWidget(self.format_label)
        h_layout2.addWidget(self.format_combo)
        h_layout2.addStretch(1)

        # 3. 保存路径
        self.dest_label = QLabel("保存路径:")
        self.dest_edit = QLineEdit()
        self.dest_edit.setPlaceholderText("请选择保存压缩文件的位置和名称")
        self.dest_button = QPushButton() # 移除文本
        self.dest_button.setIcon(save_icon) # 直接设置图标
        self.dest_button.setIconSize(icon_size)
        self.dest_button.setToolTip("选择保存路径和文件名")

        h_layout3.addWidget(self.dest_label)
        h_layout3.addWidget(self.dest_edit)
        h_layout3.addWidget(self.dest_button)

        # 4. 打包按钮
        self.pack_button = QPushButton(" 开始打包")
        self.pack_button.setIcon(pack_icon) # 直接设置图标
        self.pack_button.setIconSize(icon_size)
        self.pack_button.setObjectName("PackButton")

        # 5. 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)

        # 6. 状态标签
        self.status_label = QLabel("准备就绪")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setObjectName("StatusLabel")

        # --- 将控件添加到主布局 ---
        main_layout.addLayout(h_layout1)
        main_layout.addLayout(h_layout2)
        main_layout.addLayout(h_layout3)
        main_layout.addSpacing(20)
        main_layout.addWidget(self.pack_button)
        main_layout.addSpacing(10)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.status_label)

        self.setLayout(main_layout)

        # --- 连接信号与槽 ---
        self.source_button.clicked.connect(self.select_source_folder)
        self.dest_button.clicked.connect(self.select_dest_file)
        self.pack_button.clicked.connect(self.start_packaging)

    # --- 槽函数 (与之前相同) ---
    def select_source_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择源文件夹")
        if folder:
            self.source_edit.setText(folder)
            self.status_label.setText("已选择源文件夹")
            self.status_label.setStyleSheet("color: #A9A9A9;")

    def select_dest_file(self):
        selected_format = self.format_combo.currentText()
        format_map = {
            'zip': 'zip', 'tar': 'tar', 'gztar': 'tar.gz',
            'bztar': 'tar.bz2', 'xztar': 'tar.xz'
        }
        extension = format_map.get(selected_format, selected_format)
        filter_str = f"{selected_format.upper()} 文件 (*.{extension})"

        source_folder_path = self.source_edit.text()
        default_name = f"archive.{extension}"
        suggested_path = ""
        if source_folder_path and os.path.isdir(source_folder_path):
            folder_name = os.path.basename(source_folder_path)
            parent_dir = os.path.dirname(source_folder_path)
            suggested_path = os.path.join(parent_dir or '.', f"{folder_name}.{extension}")

        file_path, _ = QFileDialog.getSaveFileName(
            self, "选择保存位置和文件名", suggested_path, filter_str
        )

        if file_path:
            self.dest_edit.setText(file_path)
            self.status_label.setText("已选择保存路径")
            self.status_label.setStyleSheet("color: #A9A9A9;")

    def start_packaging(self):
        source_dir = self.source_edit.text()
        dest_file_full_path = self.dest_edit.text()
        archive_format = self.format_combo.currentText()

        if not source_dir or not os.path.isdir(source_dir):
            QMessageBox.warning(self, "输入错误", "请选择一个有效的源文件夹！")
            return
        if not dest_file_full_path:
            QMessageBox.warning(self, "输入错误", "请选择保存路径和文件名！")
            return

        dest_dir = os.path.dirname(dest_file_full_path)
        base_filename = os.path.basename(dest_file_full_path)
        base_name_for_shutil = dest_file_full_path
        format_map = {
            'zip': '.zip', 'tar': '.tar', 'gztar': '.tar.gz',
            'bztar': '.tar.bz2', 'xztar': '.tar.xz'
        }
        expected_ext = format_map.get(archive_format)

        if expected_ext:
            if base_name_for_shutil.lower().endswith(expected_ext):
                base_name_for_shutil = base_name_for_shutil[:-len(expected_ext)]
            else:
                print(f"警告: 选择的文件名 '{base_filename}' 可能没有预期的扩展名 '{expected_ext}'. 将直接使用 '{base_name_for_shutil}' 作为基础名。")
        else:
            base_name_for_shutil, _ = os.path.splitext(dest_file_full_path)

        try:
            os.makedirs(os.path.dirname(base_name_for_shutil), exist_ok=True)
        except OSError as e:
            QMessageBox.critical(self, "错误", f"无法创建目标目录: {os.path.dirname(base_name_for_shutil)}\n{e}")
            return

        self.pack_button.setEnabled(False)
        self.status_label.setText(f"正在打包 {archive_format}...")
        self.status_label.setStyleSheet("color: #FFD700;")
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("") # 恢复默认样式

        root_dir_for_shutil = source_dir
        self.worker = PackWorker(source_dir, base_name_for_shutil, archive_format, root_dir_for_shutil)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.on_packaging_finished)
        self.worker.error.connect(self.on_packaging_error)
        self.worker.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def on_packaging_finished(self, message):
        self.progress_bar.setValue(100)
        self.status_label.setText(message or "打包完成！")
        self.status_label.setStyleSheet("color: #90EE90;")
        self.pack_button.setEnabled(True)
        QMessageBox.information(self, "成功", message or "打包操作已成功完成！")
        self.worker = None

    def on_packaging_error(self, error_message):
        self.progress_bar.setValue(100) # 或保持0
        self.progress_bar.setStyleSheet("""
            QProgressBar::chunk {
                background-color: #DC143C; /* 猩红色 */
                border-radius: 5px;
            }
        """)
        self.status_label.setText(f"错误: {error_message}")
        self.status_label.setStyleSheet("color: #F08080;")
        self.pack_button.setEnabled(True)
        QMessageBox.critical(self, "打包失败", error_message)
        self.worker = None


# --- QSS 样式表 (与之前相同) ---
# --- QSS 样式表 ---
dark_matte_style = """
QWidget {
    background-color: #2E2E2E; /* 深灰色背景 */
    color: #E0E0E0; /* 浅灰色文字 */
    font-family: "Microsoft YaHei", "Segoe UI", Arial, sans-serif; /* 字体 */
    font-size: 12pt; /* <<< 增大全局字体大小 */
}

QLabel {
    color: #C0C0C0;
    padding: 2px;
}

QLineEdit {
    background-color: #3C3C3C;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 6px; /* 调整 padding 以匹配按钮高度 */
    color: #E0E0E0;
    min-height: 22px; /* 确保最小高度 */
}

QLineEdit:focus {
    border: 1px solid #77AADD;
}

QComboBox {
    background-color: #3C3C3C;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 6px 10px 6px 6px; /* <<< 调整垂直 padding 为 6px */
    min-width: 6em;
    color: #E0E0E0;
    min-height: 22px; /* <<< 确保最小高度与按钮一致 */
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border-left-width: 1px;
    border-left-color: #555555;
    border-left-style: solid;
    border-top-right-radius: 3px;
    border-bottom-right-radius: 3px;
    background-color: #424242;
}

QComboBox::down-arrow {
     image: url(:/qt-project.org/styles/commonstyle/images/downarraow-16.png);
     width: 10px;
     height: 10px;
}
QComboBox QAbstractItemView {
    background-color: #3C3C3C;
    border: 1px solid #555555;
    selection-background-color: #50A0D0;
    selection-color: #FFFFFF;
    color: #E0E0E0;
    padding: 4px; /* 调整下拉列表内边距 */
}

QPushButton {
    background-color: #4A4A4A;
    border: 1px solid #606060;
    border-radius: 4px;
    padding: 6px 12px; /* <<< 保持垂直 padding 为 6px */
    color: #E0E0E0;
    min-width: 30px;
    min-height: 22px; /* <<< 确保最小高度 */
}

QPushButton:hover {
    background-color: #5A5A5A;
    border-color: #777777;
}

QPushButton:pressed {
    background-color: #6A6A6A;
}

QPushButton:disabled {
    background-color: #404040;
    color: #808080;
    border-color: #505050;
}

/* === 打包按钮样式修改 === */
QPushButton#PackButton {
    font-weight: bold;
    background-color: #4CAF50; /* <<< 主要绿色 */
    color: #FFFFFF; /* 白色文字 */
    min-width: 80px;
}
QPushButton#PackButton:hover {
    background-color: #66BB6A; /* <<< 悬停时稍亮的绿色 */
    color: #FFFFFF;
}
QPushButton#PackButton:pressed {
    background-color: #388E3C; /* <<< 按下时稍深的绿色 */
    color: #FFFFFF;
}
QPushButton#PackButton:disabled {
    background-color: #A5D6A7; /* <<< 禁用时浅绿色背景 */
    color: #616161; /* <<< 禁用时深灰色文字 */
    border-color: #81C784;
}
/* ======================== */


QProgressBar {
    border: 1px solid #555555;
    border-radius: 5px;
    text-align: center;
    background-color: #3C3C3C;
    color: #E0E0E0;
    min-height: 20px; /* 进度条高度 */
}

QProgressBar::chunk {
    background-color: #50A0D0; /* 默认蓝色进度 */
    border-radius: 5px;
}

/* 错误状态下的进度条填充颜色 (通过代码设置) */
/* QProgressBar::chunk { background-color: #DC143C; } */


QLabel#StatusLabel {
    color: #A9A9A9;
    font-size: 10pt; /* <<< 状态标签字体也稍大一些 */
    padding: 5px;
}

QMessageBox {
    background-color: #333333;
}

QMessageBox QLabel {
    color: #E0E0E0;
    font-size: 11pt; /* 消息框字体也同步 */
}

QMessageBox QPushButton {
    background-color: #4A4A4A;
    border: 1px solid #606060;
    border-radius: 4px;
    padding: 6px 12px;
    color: #E0E0E0;
    min-width: 70px;
    min-height: 22px; /* 消息框按钮高度 */
}
QMessageBox QPushButton:hover {
    background-color: #5A5A5A;
}
QMessageBox QPushButton:pressed {
    background-color: #6A6A6A;
}

QToolTip {
    background-color: #424242;
    color: #E0E0E0;
    border: 1px solid #606060;
    padding: 4px;
    border-radius: 3px;
    opacity: 230;
    font-size: 10pt; /* Tooltip 字体 */
}
"""

# --- 程序入口 ---
if __name__ == '__main__':
    app = QApplication(sys.argv)

    # --- 应用 QSS 样式 ---
    app.setStyleSheet(dark_matte_style)

    ex = PackApp()
    ex.show()
    sys.exit(app.exec())