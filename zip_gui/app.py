import sys
import os
import shutil
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QRadioButton,
    QProgressBar,
    QFileDialog,
    QMessageBox,
    QGroupBox,
    QFrame,
)
from PySide6.QtCore import Qt, QThread, Signal, QSize
from PySide6.QtGui import QIcon
import qtawesome as qta
from .style import load_stylesheet
from PySide6.QtWidgets import QStackedWidget


class PackWorker(QThread):
    finished = Signal(str)
    error = Signal(str)
    progress = Signal(int)

    def __init__(
        self, dest_file_base, archive_format, root_dir_for_shutil, base_dir_to_archive
    ):
        super().__init__()
        self.dest_file_base = dest_file_base
        self.archive_format = archive_format
        self.root_dir_for_shutil = root_dir_for_shutil  # 这是父目录
        self.base_dir_to_archive = base_dir_to_archive  # 这是要打包的文件夹名

    def run(self):
        try:
            self.progress.emit(10)
            # 更新打印信息以反映实际使用的参数
            print(
                f"开始打包: base_name='{self.dest_file_base}', format='{self.archive_format}', "
                f"root_dir='{self.root_dir_for_shutil}', base_dir='{self.base_dir_to_archive}'"
            )
            # 修改 shutil.make_archive 调用
            archive_path = shutil.make_archive(
                base_name=self.dest_file_base,
                format=self.archive_format,
                root_dir=self.root_dir_for_shutil,  # 使用父目录作为 root_dir
                base_dir=self.base_dir_to_archive,  # 使用文件夹名作为 base_dir
            )
            self.progress.emit(100)
            self.finished.emit(f"成功打包到: {archive_path}")
        except Exception as e:
            print(f"打包出错: {e}")
            # 考虑添加更具体的错误信息，例如检查 root_dir 和 base_dir 是否有效
            if isinstance(e, FileNotFoundError):
                self.error.emit(
                    f"打包失败: 找不到源路径 '{os.path.join(self.root_dir_for_shutil, self.base_dir_to_archive)}'"
                )
            else:
                self.error.emit(f"打包失败: {str(e)}")
        finally:
            pass


class UnpackWorker(QThread):
    finished = Signal(str)
    error = Signal(str)
    progress = Signal(int)

    def __init__(self, archive_file, extract_dir):
        super().__init__()
        self.archive_file = archive_file
        self.extract_dir = extract_dir

    def run(self):
        try:
            self.progress.emit(10)
            print(
                f"开始解压: archive='{self.archive_file}', extract_dir='{self.extract_dir}'"
            )

            os.makedirs(self.extract_dir, exist_ok=True)

            shutil.unpack_archive(self.archive_file, self.extract_dir)

            self.progress.emit(100)
            self.finished.emit(f"成功解压到: {self.extract_dir}")
        except Exception as e:
            print(f"解压出错: {e}")
            error_msg = f"解压失败: {str(e)}"
            if isinstance(e, shutil.ReadError):
                error_msg = f"解压失败: 文件 '{os.path.basename(self.archive_file)}' 可能不是受支持的压缩格式或已损坏。"
            elif isinstance(e, FileNotFoundError):
                error_msg = f"解压失败: 找不到文件 '{self.archive_file}'。"
            elif isinstance(e, PermissionError):
                error_msg = f"解压失败: 没有权限写入目标文件夹 '{self.extract_dir}'。"

            self.error.emit(error_msg)
        finally:
            pass


class PackApp(QWidget):
    MODE_PACK = 0
    MODE_UNPACK = 1

    def __init__(self):
        super().__init__()
        self.worker = None
        self.current_mode = self.MODE_PACK
        self.initUI()

    def initUI(self):
        self.setWindowTitle("简易打包解压工具")
        self.setGeometry(300, 300, 450, 400)  # 调整窗口大小

        # --- 主布局 ---
        main_layout = QVBoxLayout()

        # --- 模式选择 ---
        mode_layout = QHBoxLayout()
        self.pack_radio = QRadioButton("打包模式")
        self.unpack_radio = QRadioButton("解压模式")
        self.pack_radio.setChecked(True)  # 默认选中打包
        self.pack_radio.toggled.connect(self.switch_mode)

        mode_layout.addWidget(self.pack_radio)
        mode_layout.addWidget(self.unpack_radio)
        mode_layout.addStretch(1)

        main_layout.addLayout(mode_layout)

        # --- 分隔线 ---
        line1 = QFrame()
        line1.setFrameShape(QFrame.Shape.HLine)
        line1.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(line1)

        # --- 打包控件容器 ---
        self.pack_group = QGroupBox("打包选项")
        pack_layout = QGridLayout()

        # 图标
        icon_size = QSize(20, 20)
        icon_color = "#A9A9A9"
        icon_color_active = "#E0E0E0"
        folder_icon = qta.icon(
            "fa5s.folder-open", color=icon_color, color_active=icon_color_active
        )
        save_icon = qta.icon(
            "fa5s.save", color=icon_color, color_active=icon_color_active
        )
        pack_icon = qta.icon(
            "fa5s.compress-alt", color=icon_color, color_active=icon_color_active
        )
        unpack_icon = qta.icon(
            "fa5s.expand-alt", color=icon_color, color_active=icon_color_active
        )  # 解压图标
        archive_icon = qta.icon(
            "fa5s.file-archive", color=icon_color, color_active=icon_color_active
        )  # 压缩文件图标
        extract_folder_icon = qta.icon(
            "fa5s.folder-plus", color=icon_color, color_active=icon_color_active
        )

        self.source_label = QLabel("源文件/文件夹:")
        self.source_edit = QLineEdit()
        self.source_edit.setPlaceholderText("选择文件夹或输入文件路径")
        self.source_button = QPushButton()
        self.source_button.setIcon(folder_icon)
        self.source_button.setIconSize(icon_size)
        self.source_button.setToolTip("选择源文件夹 (或手动输入文件路径)")
        pack_layout.addWidget(self.source_label, 0, 0)
        pack_layout.addWidget(self.source_edit, 0, 1)
        pack_layout.addWidget(self.source_button, 0, 2)

        self.format_label = QLabel("压缩类型:")
        self.format_combo = QComboBox()
        supported_formats = [fmt[0] for fmt in shutil.get_archive_formats()]
        supported_formats.reverse()
        self.format_combo.addItems(supported_formats)
        pack_layout.addWidget(self.format_label, 1, 0)
        pack_layout.addWidget(self.format_combo, 1, 1)

        # 打包: 保存路径
        self.dest_label = QLabel("保存路径:")
        self.dest_edit = QLineEdit()
        self.dest_edit.setPlaceholderText("选择压缩文件的保存位置和名称")
        self.dest_button = QPushButton()
        self.dest_button.setIcon(save_icon)
        self.dest_button.setIconSize(icon_size)
        self.dest_button.setToolTip("选择保存路径和文件名")
        pack_layout.addWidget(self.dest_label, 2, 0)
        pack_layout.addWidget(self.dest_edit, 2, 1)
        pack_layout.addWidget(self.dest_button, 2, 2)

        self.pack_group.setLayout(pack_layout)

        # --- 解压控件容器 ---
        self.unpack_group = QGroupBox("解压选项")
        unpack_layout = QGridLayout()

        # 解压: 压缩文件
        self.archive_label = QLabel("压缩文件:")
        self.archive_edit = QLineEdit()
        self.archive_edit.setPlaceholderText("选择要解压的压缩文件")
        self.archive_button = QPushButton()
        self.archive_button.setIcon(archive_icon)
        self.archive_button.setIconSize(icon_size)
        self.archive_button.setToolTip("选择压缩文件")
        unpack_layout.addWidget(self.archive_label, 0, 0)
        unpack_layout.addWidget(self.archive_edit, 0, 1)
        unpack_layout.addWidget(self.archive_button, 0, 2)

        # 解压: 目标文件夹
        self.extract_label = QLabel("目标文件夹:")
        self.extract_edit = QLineEdit()
        self.extract_edit.setPlaceholderText("选择解压文件的存放位置")
        self.extract_button = QPushButton()
        self.extract_button.setIcon(extract_folder_icon)
        self.extract_button.setIconSize(icon_size)
        self.extract_button.setToolTip("选择目标文件夹")
        unpack_layout.addWidget(self.extract_label, 1, 0)
        unpack_layout.addWidget(self.extract_edit, 1, 1)
        unpack_layout.addWidget(self.extract_button, 1, 2)

        self.unpack_group.setLayout(unpack_layout)
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self.pack_group)  # 添加打包页面 (索引 0)
        self.stacked_widget.addWidget(self.unpack_group)

        main_layout.addWidget(self.stacked_widget)

        # --- 公共控件 ---
        # 主操作按钮
        self.action_button = QPushButton(" 开始打包")  # 初始文本
        self.action_button.setIcon(pack_icon)  # 初始图标
        self.action_button.setIconSize(icon_size)
        self.action_button.setObjectName("ActionButton")  # 使用新的 ObjectName

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)

        # 状态标签
        self.status_label = QLabel("准备就绪")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setObjectName("StatusLabel")

        # --- 将公共控件添加到主布局 ---
        main_layout.addSpacing(15)
        main_layout.addWidget(self.action_button)
        main_layout.addSpacing(10)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.status_label)
        main_layout.addStretch(1)  # 添加伸缩因子，让控件靠上

        self.setLayout(main_layout)

        # --- 连接信号与槽 ---
        self.source_button.clicked.connect(self.select_source_path)
        self.dest_button.clicked.connect(self.select_dest_file)
        self.archive_button.clicked.connect(self.select_archive_file)
        self.extract_button.clicked.connect(self.select_extract_folder)
        self.action_button.clicked.connect(self.start_action)  # 连接到统一的启动函数

        # --- 更新图标 (在 switch_mode 中处理) ---
        self.update_action_button_style()  # 初始化按钮样式

    # --- 模式切换槽函数 ---
    def switch_mode(self, checked):
        if self.pack_radio.isChecked():
            if self.current_mode != self.MODE_PACK:
                self.current_mode = self.MODE_PACK
                self.stacked_widget.setCurrentWidget(self.pack_group)  # 切换到打包页面
                self.status_label.setText("切换到打包模式")
                self.clear_inputs()
                self.update_action_button_style()
        else:  # unpack_radio is checked
            if self.current_mode != self.MODE_UNPACK:
                self.current_mode = self.MODE_UNPACK
                self.stacked_widget.setCurrentWidget(
                    self.unpack_group
                )  # 切换到解压页面
                self.status_label.setText("切换到解压模式")
                self.clear_inputs()
                self.update_action_button_style()

    def update_action_button_style(self):
        """根据当前模式更新主操作按钮的文本和图标"""
        icon_size = QSize(20, 20)
        icon_color = "#A9A9A9"
        icon_color_active = "#E0E0E0"
        if self.current_mode == self.MODE_PACK:
            self.action_button.setText(" 开始打包")
            try:
                pack_icon = qta.icon(
                    "fa5s.compress-alt",
                    color=icon_color,
                    color_active=icon_color_active,
                )
                self.action_button.setIcon(pack_icon)
            except Exception:
                self.action_button.setIcon(QIcon())
            self.action_button.setIconSize(icon_size)
            # 恢复打包按钮的绿色样式 (如果 QSS 中定义了 ActionButton)
            self.action_button.setStyleSheet("")  # 清除可能存在的特定样式，让 QSS 生效
        else:  # MODE_UNPACK
            self.action_button.setText(" 开始解压")
            try:
                unpack_icon = qta.icon(
                    "fa5s.expand-alt", color=icon_color, color_active=icon_color_active
                )
                self.action_button.setIcon(unpack_icon)
            except Exception:
                self.action_button.setIcon(QIcon())
            self.action_button.setIconSize(icon_size)
            self.action_button.setStyleSheet("")  # 清除可能存在的特定样式，让 QSS 生效

    def clear_inputs(self):
        """清空所有输入框"""
        self.source_edit.clear()
        self.dest_edit.clear()
        self.archive_edit.clear()
        self.extract_edit.clear()
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("")  # 清除进度条样式
        self.status_label.setStyleSheet("color: #A9A9A9;")  # 恢复默认颜色

    def select_source_path(self):
        folder = QFileDialog.getExistingDirectory(self, "选择源文件夹")
        if folder:
            self.source_edit.setText(folder)
            self.status_label.setText("已选择源文件夹")
            self.status_label.setStyleSheet("color: #A9A9A9;")

    def select_dest_file(self):
        selected_format = self.format_combo.currentText()
        format_map = {
            "zip": "zip",
            "tar": "tar",
            "gztar": "tar.gz",
            "bztar": "tar.bz2",
            "xztar": "tar.xz",
        }
        extension = format_map.get(selected_format, selected_format)
        filter_str = f"{selected_format.upper()} 文件 (*.{extension})"

        source_path = self.source_edit.text()  # 使用 source_path 变量名
        suggested_path = ""
        if source_path and os.path.exists(
            source_path
        ):  # 检查路径是否存在 (文件或文件夹)
            base_name = os.path.basename(source_path)  # 获取基本名称 (文件或文件夹名)
            parent_dir = os.path.dirname(source_path)
            # 如果 base_name 为空 (例如 C:\)，则使用默认名称或不建议
            if base_name:
                suggested_path = os.path.join(
                    parent_dir or ".", f"{base_name}.{extension}"
                )
            else:
                # 对于根目录等情况，可以提供一个默认名称
                suggested_path = os.path.join(parent_dir or ".", f"archive.{extension}")

        file_path, _ = QFileDialog.getSaveFileName(
            self, "选择保存位置和文件名", suggested_path, filter_str
        )
        if file_path:
            self.dest_edit.setText(file_path)
            self.status_label.setText("已选择保存路径")
            self.status_label.setStyleSheet("color: #A9A9A9;")

    def select_archive_file(self):
        filters = "压缩文件 (*.zip *.rar *.7z *.tar *.gz *.bz2 *.xz);;所有文件 (*.*)"
        file_path, _ = QFileDialog.getOpenFileName(self, "选择压缩文件", "", filters)
        if file_path:
            self.archive_edit.setText(file_path)
            self.status_label.setText("已选择压缩文件")
            self.status_label.setStyleSheet("color: #A9A9A9;")

    def select_extract_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择目标文件夹")
        if folder:
            self.extract_edit.setText(folder)
            self.status_label.setText("已选择目标文件夹")
            self.status_label.setStyleSheet("color: #A9A9A9;")

    def start_action(self):
        """根据当前模式启动打包或解压"""
        self.action_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("")

        if self.current_mode == self.MODE_PACK:
            self.start_packaging()
        else:  # MODE_UNPACK
            self.start_unpacking()

    def start_packaging(self):
        # 使用更通用的变量名 source_path
        source_path = self.source_edit.text()
        dest_file_full_path = self.dest_edit.text()
        archive_format = self.format_combo.currentText()

        # 检查路径是否存在，无论是文件还是文件夹
        if not source_path or not os.path.exists(source_path):
            QMessageBox.warning(
                self, "输入错误", "请选择或输入一个有效的源文件或文件夹！"
            )
            self.action_button.setEnabled(True)
            return

        if not dest_file_full_path:
            QMessageBox.warning(self, "输入错误", "请选择保存路径和文件名！")
            self.action_button.setEnabled(True)
            return

        # 获取源路径的父目录
        parent_dir = os.path.dirname(source_path)
        # 获取源路径的基本名称 (文件名或文件夹名)
        item_to_archive = os.path.basename(source_path)

        # 处理特殊情况：
        # 1. 如果选择的是驱动器根目录 (例如 C:\), basename 会是空
        if not item_to_archive:
            QMessageBox.warning(self, "输入错误", "不支持直接打包驱动器根目录。")
            self.action_button.setEnabled(True)
            return

        # 2. 如果父目录为空 (例如只输入了文件名/文件夹名，表示在当前目录下)
        #    os.path.dirname("myfile.txt") 返回 ''
        #    shutil.make_archive 的 root_dir 需要一个实际路径，'.' 代表当前工作目录
        if not parent_dir:
            parent_dir = ".."

        # --- (处理目标文件名的逻辑保持不变) ---
        dest_dir = os.path.dirname(dest_file_full_path)
        base_filename = os.path.basename(dest_file_full_path)
        base_name_for_shutil = dest_file_full_path
        format_map = {
            "zip": ".zip",
            "tar": ".tar",
            "gztar": ".tar.gz",
            "bztar": ".tar.bz2",
            "xztar": ".tar.xz",
        }
        expected_ext = format_map.get(archive_format)

        if expected_ext:
            if base_name_for_shutil.lower().endswith(expected_ext):
                base_name_for_shutil = base_name_for_shutil[: -len(expected_ext)]
            else:
                print(
                    f"警告: 文件名 '{base_filename}' 没有预期扩展名 '{expected_ext}'."
                )
        # --- (目标目录创建逻辑保持不变) ---
        try:
            os.makedirs(os.path.dirname(base_name_for_shutil), exist_ok=True)
        except OSError as e:
            QMessageBox.critical(
                self,
                "错误",
                f"无法创建目标目录: {os.path.dirname(base_name_for_shutil)}\n{e}",
            )
            self.action_button.setEnabled(True)
            return

        self.status_label.setText(f"正在打包 {archive_format}...")
        self.status_label.setStyleSheet("color: #FFD700;")  # 黄色

        # 使用计算好的 parent_dir 和 item_to_archive
        self.worker = PackWorker(
            base_name_for_shutil,
            archive_format,
            parent_dir,  # root_dir: 父目录
            item_to_archive,  # base_dir: 要打包的文件或文件夹名
        )

        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.on_action_finished)
        self.worker.error.connect(self.on_action_error)
        self.worker.start()

    def start_unpacking(self):
        archive_file = self.archive_edit.text()
        extract_dir = self.extract_edit.text()

        if not archive_file or not os.path.isfile(archive_file):
            QMessageBox.warning(self, "输入错误", "请选择一个有效的压缩文件！")
            self.action_button.setEnabled(True)
            return
        if not extract_dir:
            QMessageBox.warning(self, "输入错误", "请选择目标文件夹！")
            self.action_button.setEnabled(True)
            return

        if os.path.isdir(extract_dir) and os.listdir(extract_dir):
            reply = QMessageBox.question(
                self,
                "确认",
                f"目标文件夹 '{extract_dir}' 已存在且非空，是否覆盖?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.No:
                self.action_button.setEnabled(True)
                return

        self.status_label.setText(f"正在解压 {os.path.basename(archive_file)}...")
        self.status_label.setStyleSheet("color: #FFD700;")  # 黄色

        self.worker = UnpackWorker(archive_file, extract_dir)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.on_action_finished)  # 连接到通用完成槽
        self.worker.error.connect(self.on_action_error)  # 连接到通用错误槽
        self.worker.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def on_action_finished(self, message):
        """处理打包或解压成功完成"""
        self.progress_bar.setValue(100)
        self.status_label.setText(message or "操作完成！")
        self.status_label.setStyleSheet("color: #90EE90;")  # 浅绿色
        self.action_button.setEnabled(True)
        QMessageBox.information(self, "成功", message or "操作已成功完成！")
        self.worker = None

    def on_action_error(self, error_message):
        """处理打包或解压过程中发生的错误"""
        self.progress_bar.setValue(100)  # 或保持0
        self.progress_bar.setStyleSheet("""
            QProgressBar::chunk {
                background-color: #DC143C; /* 猩红色 */
                border-radius: 5px;
            }
        """)
        self.status_label.setText(f"错误: {error_message}")
        self.status_label.setStyleSheet("color: #F08080;")  # 浅珊瑚色
        self.action_button.setEnabled(True)
        QMessageBox.critical(self, "操作失败", error_message)
        self.worker = None


def run():
    app = QApplication(sys.argv)
    style_sheet = load_stylesheet()
    if style_sheet:
        app.setStyleSheet(style_sheet)
    ex = PackApp()
    ex.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run()
