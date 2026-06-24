import pytest
from PySide6.QtCore import QDir
from zip_gui.presenter import NavigationPresenter
from zip_gui.archive_model import ArchiveModel
from zip_gui.archive_handler import ArchiveInfo, ArchiveEntry

class MockView:
    def __init__(self):
        self.model = None
        self.root_index = None
        self.sorting_enabled = False
        self.column_widths_reset = False
        self.address_path = ""
        self.address_in_archive = False
        self.address_archive_path = ""
        self.address_archive_internal = ""
        self.messages = []
        self.progress_visible = False
        self.progress_value = 0
        self.status_text = ""
        self.action_states_filesystem = True
        self.status_count_updated = False
        
        # Dialog inputs return values
        self.save_dialog_result = ("", "")
        self.directory_dialog_result = ""
        self.input_dialog_result = ("", False)
        self.confirm_dialog_result = True
        self.selected_fs_paths = []
        self.selected_archive_entries = []
        self.project_info_shown = False

    def set_model(self, model):
        self.model = model

    def set_root_index(self, index):
        self.root_index = index

    def set_sorting_enabled(self, enabled):
        self.sorting_enabled = enabled

    def reset_column_widths(self):
        self.column_widths_reset = True

    def update_address_bar(self, path, in_archive, archive_path, archive_internal):
        self.address_path = path
        self.address_in_archive = in_archive
        self.address_archive_path = archive_path
        self.address_archive_internal = archive_internal

    def get_address_path(self):
        return self.address_path

    def show_message(self, title, message, icon_type="info"):
        self.messages.append((title, message, icon_type))

    def show_progress_bar(self, visible):
        self.progress_visible = visible

    def set_progress_value(self, value):
        self.progress_value = value

    def set_status_text(self, text):
        self.status_text = text

    def prompt_save_dialog(self, title, default_path, filter_str):
        return self.save_dialog_result

    def prompt_directory_dialog(self, title):
        return self.directory_dialog_result

    def prompt_input_dialog(self, title, label, text):
        return self.input_dialog_result

    def confirm_dialog(self, title, text):
        return self.confirm_dialog_result

    def get_selected_fs_paths(self):
        return self.selected_fs_paths

    def get_selected_archive_entries(self):
        return self.selected_archive_entries

    def update_action_states(self, is_filesystem):
        self.action_states_filesystem = is_filesystem

    def update_status_count(self):
        self.status_count_updated = True

    def show_project_info(self):
        self.project_info_shown = True


class DummyModel:
    def __init__(self):
        pass
    def index(self, path):
        return path


def test_presenter_navigation(qtbot, monkeypatch):
    """Test presenter handles mode transitions and view updates correctly."""
    view = MockView()
    archive_model = ArchiveModel()
    fs_model = DummyModel()
    proxy = DummyModel()
    
    presenter = NavigationPresenter(view, archive_model, fs_model, proxy)
    
    # Test filesystem navigation
    presenter.navigate_to_dir("/home/user")
    assert presenter.mode == "filesystem"
    assert view.model == fs_model
    assert view.root_index == "/home/user"
    assert view.address_path == "/home/user"
    assert view.address_in_archive is False
    assert view.action_states_filesystem is True
    
    # Test archive navigation (with dummy archive data)
    entries = [
        ArchiveEntry(filename="a.txt", is_dir=False, file_size=100, compress_size=50),
    ]
    info = ArchiveInfo(path="test.zip", format="zip", total_files=1, total_size=100, total_compressed=50, entries=entries)
    
    # Mock list_contents to return our dummy ArchiveInfo
    monkeypatch.setattr("zip_gui.presenter.list_contents", lambda path: info)
    
    presenter.navigate_into_archive("test.zip")
    assert presenter.mode == "archive"
    assert presenter.current_archive_path == "test.zip"
    assert view.model == proxy
    assert view.address_in_archive is True
    assert view.address_archive_path == "test.zip"
    assert view.action_states_filesystem is False
    assert "压缩包" in view.status_text
    
    # Test address change behavior
    presenter.on_address_changed("__archive_root__")
    assert archive_model.current_path == ""
    assert view.address_archive_internal == ""


def test_presenter_actions_unsupported_mode(qtbot):
    """Test presenter prevents certain actions in unsupported modes."""
    view = MockView()
    archive_model = ArchiveModel()
    fs_model = DummyModel()
    proxy = DummyModel()
    
    presenter = NavigationPresenter(view, archive_model, fs_model, proxy)
    presenter.mode = "archive"
    
    # Add action is only supported in filesystem mode
    presenter.on_add()
    assert len(view.messages) == 1
    assert view.messages[0][0] == "提示"
    assert presenter.task_manager.has_active_tasks() is False
