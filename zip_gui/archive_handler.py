"""Unified archive reading/writing using zipfile and tarfile."""

from __future__ import annotations

import os
import tarfile
import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal


@dataclass
class ArchiveEntry:
    """Represents a single entry inside an archive."""

    filename: str  # full path inside archive
    is_dir: bool = False
    file_size: int = 0
    compress_size: int = 0
    date_time: datetime | None = None
    crc: str = ""

    @property
    def basename(self) -> str:
        name = self.filename.rstrip("/")
        return os.path.basename(name)

    @property
    def parent(self) -> str:
        name = self.filename.rstrip("/")
        p = os.path.dirname(name)
        return p + "/" if p else ""


@dataclass
class ArchiveInfo:
    """Summary info about an archive."""

    path: str
    format: str  # 'zip', 'tar', 'tar.gz', 'tar.bz2', 'tar.xz'
    total_files: int = 0
    total_size: int = 0
    total_compressed: int = 0
    entries: list[ArchiveEntry] = field(default_factory=list)


ArchiveFormat = Literal["zip", "tar", "tar.gz", "tar.bz2", "tar.xz"]

# Mapping file extensions to archive formats
_EXT_MAP: dict[str, ArchiveFormat] = {
    ".zip": "zip",
    ".tar": "tar",
    ".tar.gz": "tar.gz",
    ".tgz": "tar.gz",
    ".tar.bz2": "tar.bz2",
    ".tbz2": "tar.bz2",
    ".tar.xz": "tar.xz",
    ".txz": "tar.xz",
    ".gz": "tar.gz",
    ".bz2": "tar.bz2",
    ".xz": "tar.xz",
}

_SUPPORTED_EXTENSIONS = tuple(_EXT_MAP.keys())


def is_archive(path: str) -> bool:
    """Check if a file path looks like a supported archive."""
    lower = path.lower()
    return any(lower.endswith(ext) for ext in _SUPPORTED_EXTENSIONS)


def detect_format(path: str) -> ArchiveFormat | None:
    """Detect the archive format from the file extension."""
    lower = path.lower()
    # Check multi-part extensions first (e.g., .tar.gz before .gz)
    for ext in sorted(_EXT_MAP.keys(), key=len, reverse=True):
        if lower.endswith(ext):
            return _EXT_MAP[ext]
    return None


def list_contents(path: str) -> ArchiveInfo:
    """List all entries in an archive. Returns ArchiveInfo with entries."""
    fmt = detect_format(path)
    if fmt is None:
        raise ValueError(f"Unsupported archive format: {path}")

    if fmt == "zip":
        return _list_zip(path)
    else:
        return _list_tar(path, fmt)


def extract_all(archive_path: str, dest_dir: str, progress_callback=None) -> None:
    """Extract all files from an archive to dest_dir."""
    fmt = detect_format(archive_path)
    if fmt == "zip":
        _extract_zip(archive_path, dest_dir, progress_callback=progress_callback)
    else:
        _extract_tar(archive_path, dest_dir, progress_callback=progress_callback)


def extract_files(
    archive_path: str, entries: list[str], dest_dir: str, progress_callback=None
) -> None:
    """Extract specific files from an archive."""
    fmt = detect_format(archive_path)
    if fmt == "zip":
        _extract_zip(archive_path, dest_dir, entries, progress_callback)
    else:
        _extract_tar(archive_path, dest_dir, entries, progress_callback)


def create_archive(
    files: list[str],
    dest_path: str,
    base_dir: str = "",
    fmt: ArchiveFormat = "zip",
    progress_callback=None,
) -> str:
    """Create a new archive from a list of files/directories."""
    if fmt == "zip":
        return _create_zip(files, dest_path, base_dir, progress_callback)
    else:
        return _create_tar(files, dest_path, base_dir, fmt, progress_callback)


def add_to_archive(
    archive_path: str, files: list[str], base_dir: str = ""
) -> None:
    """Add files to an existing archive (zip only)."""
    fmt = detect_format(archive_path)
    if fmt != "zip":
        raise ValueError("Adding files is only supported for ZIP archives")

    with zipfile.ZipFile(archive_path, "a", zipfile.ZIP_DEFLATED) as zf:
        for fpath in files:
            if os.path.isdir(fpath):
                for root, _dirs, filenames in os.walk(fpath):
                    for fn in filenames:
                        full = os.path.join(root, fn)
                        arcname = os.path.relpath(full, base_dir) if base_dir else fn
                        zf.write(full, arcname)
            else:
                arcname = os.path.relpath(fpath, base_dir) if base_dir else os.path.basename(fpath)
                zf.write(fpath, arcname)


def test_archive(path: str) -> tuple[bool, str]:
    """Test archive integrity. Returns (ok, message)."""
    fmt = detect_format(path)
    if fmt == "zip":
        try:
            with zipfile.ZipFile(path, "r") as zf:
                bad = zf.testzip()
                if bad is not None:
                    return False, f"损坏的文件: {bad}"
                return True, f"压缩包完好，共 {len(zf.namelist())} 个文件"
        except Exception as e:
            return False, f"测试失败: {e}"
    else:
        try:
            mode = _tar_mode(fmt, "r")
            with tarfile.open(path, mode) as tf:
                members = tf.getmembers()
                return True, f"压缩包完好，共 {len(members)} 个文件"
        except Exception as e:
            return False, f"测试失败: {e}"


# --- Internal helpers ---


def _list_zip(path: str) -> ArchiveInfo:
    info = ArchiveInfo(path=path, format="zip")
    with zipfile.ZipFile(path, "r") as zf:
        for zi in zf.infolist():
            entry = ArchiveEntry(
                filename=zi.filename,
                is_dir=zi.is_dir(),
                file_size=zi.file_size,
                compress_size=zi.compress_size,
                date_time=datetime(*zi.date_time) if zi.date_time else None,
                crc=f"{zi.CRC:08X}" if zi.CRC else "",
            )
            info.entries.append(entry)
            info.total_files += 1
            info.total_size += zi.file_size
            info.total_compressed += zi.compress_size
    return info


def _list_tar(path: str, fmt: ArchiveFormat) -> ArchiveInfo:
    info = ArchiveInfo(path=path, format=fmt)
    mode = _tar_mode(fmt, "r")
    with tarfile.open(path, mode) as tf:
        for member in tf.getmembers():
            entry = ArchiveEntry(
                filename=member.name + ("/" if member.isdir() else ""),
                is_dir=member.isdir(),
                file_size=member.size,
                compress_size=member.size,  # tar doesn't track compressed size per file
                date_time=datetime.fromtimestamp(member.mtime) if member.mtime else None,
            )
            info.entries.append(entry)
            info.total_files += 1
            info.total_size += member.size
    return info


def _extract_zip(
    path: str, dest: str, members: list[str] | None = None, progress_callback=None
) -> None:
    os.makedirs(dest, exist_ok=True)
    with zipfile.ZipFile(path, "r") as zf:
        items = members if members else zf.namelist()
        total = len(items)
        for i, name in enumerate(items):
            zf.extract(name, dest)
            if progress_callback and total > 0:
                progress_callback(int((i + 1) / total * 100))


def _extract_tar(
    path: str, dest: str, members: list[str] | None = None, progress_callback=None
) -> None:
    os.makedirs(dest, exist_ok=True)
    fmt = detect_format(path)
    mode = _tar_mode(fmt, "r")  # type: ignore[arg-type]
    with tarfile.open(path, mode) as tf:
        if members:
            tar_members = [tf.getmember(m) for m in members]
        else:
            tar_members = tf.getmembers()
        total = len(tar_members)
        for i, member in enumerate(tar_members):
            tf.extract(member, dest, filter="data")
            if progress_callback and total > 0:
                progress_callback(int((i + 1) / total * 100))


def _create_zip(
    files: list[str], dest: str, base_dir: str, progress_callback=None
) -> str:
    if not dest.lower().endswith(".zip"):
        dest += ".zip"

    all_files = _collect_files(files)
    total = len(all_files)

    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zf:
        for i, fpath in enumerate(all_files):
            arcname = os.path.relpath(fpath, base_dir) if base_dir else os.path.basename(fpath)
            zf.write(fpath, arcname)
            if progress_callback and total > 0:
                progress_callback(int((i + 1) / total * 100))
    return dest


def _create_tar(
    files: list[str],
    dest: str,
    base_dir: str,
    fmt: ArchiveFormat,
    progress_callback=None,
) -> str:
    mode = _tar_mode(fmt, "w")
    all_files = _collect_files(files)
    total = len(all_files)

    with tarfile.open(dest, mode) as tf:
        for i, fpath in enumerate(all_files):
            arcname = os.path.relpath(fpath, base_dir) if base_dir else os.path.basename(fpath)
            tf.add(fpath, arcname)
            if progress_callback and total > 0:
                progress_callback(int((i + 1) / total * 100))
    return dest


def _tar_mode(fmt: ArchiveFormat | None, prefix: str) -> str:
    """Get tarfile open mode string from format."""
    suffix_map = {
        "tar": "",
        "tar.gz": ":gz",
        "tar.bz2": ":bz2",
        "tar.xz": ":xz",
    }
    return prefix + suffix_map.get(fmt or "tar", "")


def _collect_files(paths: list[str]) -> list[str]:
    """Recursively collect all file paths from a list of files/directories."""
    result = []
    for p in paths:
        if os.path.isdir(p):
            for root, _dirs, filenames in os.walk(p):
                for fn in filenames:
                    result.append(os.path.join(root, fn))
        elif os.path.isfile(p):
            result.append(p)
    return result


def format_size(size: int) -> str:
    """Format byte size to human-readable string."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024:
            return f"{size:.1f} {unit}" if unit != "B" else f"{size} {unit}"
        size /= 1024  # type: ignore[assignment]
    return f"{size:.1f} PB"
