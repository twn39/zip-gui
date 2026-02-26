# ZipGUI - Simple Archive Utility

[![PyPI version](https://badge.fury.io/py/zip_gui.svg)](https://badge.fury.io/py/zip_gui)
[![Python Version](https://img.shields.io/badge/python-3.11%7E3.14-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-PySide6-informational)](https://www.qt.io/qt-for-python)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE) <!-- 你可以添加一个 LICENSE 文件 -->

A clean and straightforward graphical interface for compressing (packing) and extracting (unpacking) archive files, built with Python and PySide6.

<div align="center">
  <img src="./screen.png" alt="图片描述" width="500"/>
</div>

## Overview

ZipGUI provides an intuitive user interface to manage your archive files effortlessly. 
Leveraging Python's built-in `shutil` module, it supports common archive formats like ZIP, TAR, GZ, BZ2, and XZ. 
Whether you need to quickly compress a folder or extract an archive, ZipGUI simplifies the process with visual feedback.

## ✨ Features

*   **Dual Mode Operation:** Easily switch between **Packing** (compressing files/folders) and **Unpacking** (extracting archives).
*   **Multiple Format Support:** Compresses to `zip`, `tar`, `gztar`, `bztar`, `xztar` formats.
*   **User-Friendly Interface:** Simple layout with clear options for selecting source paths, destination paths, and archive formats.

## 📋 Requirements

*   **Python:** 3.11 or higher (支持 3.11 ~ 3.14)
*   **PySide6:** The Qt for Python framework.

## 🚀 Installation

```bash
# 安装依赖
uv sync

# 运行应用
uv run zip-gui
```

## 📦 Building Executable

You can create a standalone executable using PyInstaller.

```bash
# 安装开发依赖（包含 PyInstaller）
uv sync --group dev

# 使用 spec 文件打包（推荐）
uv run pyinstaller --clean ZipGUI.spec

# 或者简单的单文件打包
uv run pyinstaller --onefile --windowed --name="ZipGUI" zip_gui/app.py
```

The executable will be located in the `dist` folder.

- **macOS:** `dist/ZipGUI.app`
- **Windows:** `dist/ZipGUI.exe`
- **Linux:** `dist/ZipGUI`

## 🤝 Contributing

Contributions are welcome! If you have suggestions for improvements or find any bugs, please feel free to open an issue or submit a pull request.

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

## 📄 License

Distributed under the MIT License. 