import pytest
from PySide6.QtCore import Qt
from zip_gui.archive_model import ArchiveModel
from zip_gui.archive_handler import ArchiveInfo, ArchiveEntry

def test_archive_model_navigation(qtbot):
    """Test standard file navigation and parent folder backtracking."""
    model = ArchiveModel()
    
    entries = [
        ArchiveEntry(filename="a/b/c.txt", is_dir=False, file_size=100, compress_size=50),
        ArchiveEntry(filename="a/b/d.txt", is_dir=False, file_size=200, compress_size=100),
        ArchiveEntry(filename="a/e.txt", is_dir=False, file_size=300, compress_size=150),
        ArchiveEntry(filename="f.txt", is_dir=False, file_size=400, compress_size=200),
        ArchiveEntry(filename="a/b/", is_dir=True, file_size=0, compress_size=0),  # explicit directory
    ]
    info = ArchiveInfo(path="dummy.zip", format="zip", total_files=5, total_size=1000, total_compressed=500, entries=entries)
    
    model.set_archive(info)
    
    # 1. Verify root directory contents
    assert model.rowCount() == 2
    assert model.columnCount() == 6
    
    # Check root items (sorted: directories first, then files)
    entry_0 = model.entry_at(0)  # should be directory 'a/'
    entry_1 = model.entry_at(1)  # should be file 'f.txt'
    
    assert entry_0.basename == "a"
    assert entry_0.is_dir is True
    # Aggregated size for directory 'a/' should be 100 + 200 + 300 = 600
    assert entry_0.file_size == 600
    
    assert entry_1.basename == "f.txt"
    assert entry_1.is_dir is False
    assert entry_1.file_size == 400

    # 2. Navigate to 'a/'
    model.navigate_to("a/")
    assert model.current_path == "a/"
    assert model.rowCount() == 2
    
    # Items inside 'a/' (sorted: dir 'a/b/' first, then file 'a/e.txt')
    entry_a0 = model.entry_at(0)
    entry_a1 = model.entry_at(1)
    
    assert entry_a0.basename == "b"
    assert entry_a0.is_dir is True
    assert entry_a0.file_size == 300  # a/b/c.txt + a/b/d.txt = 100 + 200 = 300
    
    assert entry_a1.basename == "e.txt"
    assert entry_a1.is_dir is False
    assert entry_a1.file_size == 300

    # 3. Navigate into 'a/b/'
    model.navigate_to("a/b/")
    assert model.current_path == "a/b/"
    assert model.rowCount() == 2
    
    # Items inside 'a/b/'
    entry_b0 = model.entry_at(0)
    entry_b1 = model.entry_at(1)
    
    assert entry_b0.basename == "c.txt"
    assert entry_b0.is_dir is False
    assert entry_b0.file_size == 100
    
    assert entry_b1.basename == "d.txt"
    assert entry_b1.is_dir is False
    assert entry_b1.file_size == 200

    # 4. Go up back to 'a/'
    assert model.go_up() is True
    assert model.current_path == "a/"
    assert model.rowCount() == 2
    
    # 5. Go up back to root
    assert model.go_up() is True
    assert model.current_path == ""
    assert model.rowCount() == 2
    
    # 6. Go up from root (should return False)
    assert model.go_up() is False
    assert model.current_path == ""


def test_archive_model_data_display(qtbot):
    """Test model data() and headerData() mapping for Qt display roles."""
    model = ArchiveModel()
    entries = [
        ArchiveEntry(filename="test.txt", is_dir=False, file_size=1024, compress_size=512, crc="ABCDEF12"),
    ]
    info = ArchiveInfo(path="dummy.zip", format="zip", total_files=1, total_size=1024, total_compressed=512, entries=entries)
    model.set_archive(info)
    
    # Verify row count
    assert model.rowCount() == 1
    
    # Verify column count and headers
    assert model.columnCount() == 6
    assert model.headerData(0, Qt.Orientation.Horizontal) == "名称"
    assert model.headerData(1, Qt.Orientation.Horizontal) == "大小"
    assert model.headerData(2, Qt.Orientation.Horizontal) == "压缩大小"
    assert model.headerData(3, Qt.Orientation.Horizontal) == "修改时间"
    assert model.headerData(4, Qt.Orientation.Horizontal) == "CRC"
    assert model.headerData(5, Qt.Orientation.Horizontal) == "类型"
    
    # Verify model indexes data mapping
    index_name = model.index(0, 0)
    index_size = model.index(0, 1)
    index_csize = model.index(0, 2)
    index_crc = model.index(0, 4)
    
    assert model.data(index_name, Qt.ItemDataRole.DisplayRole) == "test.txt"
    assert model.data(index_size, Qt.ItemDataRole.DisplayRole) == "1.0 KB"
    assert model.data(index_csize, Qt.ItemDataRole.DisplayRole) == "512 B"
    assert model.data(index_crc, Qt.ItemDataRole.DisplayRole) == "ABCDEF12"


def test_archive_model_clear(qtbot):
    """Test clear resets all internal entries and path."""
    model = ArchiveModel()
    entries = [
        ArchiveEntry(filename="test.txt", is_dir=False, file_size=1024, compress_size=512, crc="ABCDEF12"),
    ]
    info = ArchiveInfo(path="dummy.zip", format="zip", total_files=1, total_size=1024, total_compressed=512, entries=entries)
    model.set_archive(info)
    assert model.rowCount() == 1
    
    model.clear()
    assert model.rowCount() == 0
    assert model.current_path == ""
    assert model.archive_path == ""
