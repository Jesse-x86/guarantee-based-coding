"""Narrow tests for SafeFileWriter atomic write, exception rollback, and backup rotation."""

import pytest
from pathlib import Path

from gbc.app.utils.safe_file_writer import SafeFileWriter


class TestSuccessfulWrite:
    """成功写入：临时文件被 rename 到目标路径，临时文件不再存在。"""

    def test_basic_write(self, tmp_path: Path):
        target = tmp_path / "f.txt"
        writer = SafeFileWriter(target)
        with writer.open("w", encoding="utf-8") as f:
            f.write("hello")

        assert target.read_text() == "hello"
        assert list(tmp_path.glob("*.tmp")) == []

    def test_write_overwrite(self, tmp_path: Path):
        """连续写入两次，第二次覆盖第一次。"""
        target = tmp_path / "f.txt"
        target.write_text("old")
        writer = SafeFileWriter(target)
        with writer.open("w", encoding="utf-8") as f:
            f.write("new")

        assert target.read_text() == "new"
        assert list(tmp_path.glob("*.tmp")) == []


class TestExceptionRollback:
    """with 块内抛异常 → 目标文件不变，临时文件被清理，异常向外传播。"""

    def test_rollback_preserves_original(self, tmp_path: Path):
        target = tmp_path / "f.txt"
        target.write_text("original")

        writer = SafeFileWriter(target)
        with pytest.raises(ValueError, match="boom"):
            with writer.open("w", encoding="utf-8") as f:
                f.write("corrupted")
                raise ValueError("boom")

        assert target.read_text() == "original"
        assert list(tmp_path.glob("*.tmp")) == []

    def test_rollback_when_no_original(self, tmp_path: Path):
        """目标文件不存在时异常 → 不创建目标文件，临时文件清理。"""
        target = tmp_path / "f.txt"
        writer = SafeFileWriter(target)
        with pytest.raises(ValueError, match="boom"):
            with writer.open("w", encoding="utf-8") as f:
                f.write("partial")
                raise ValueError("boom")

        assert not target.exists()
        assert list(tmp_path.glob("*.tmp")) == []


class TestBackupRotation:
    """备份轮转：num_backups=N 时旧文件被改名轮转。"""

    def test_rotation_three_writes(self, tmp_path: Path):
        target = tmp_path / "data.txt"
        writer = SafeFileWriter(target, num_backups=2)

        with writer.open("w", encoding="utf-8") as f:
            f.write("v1")
        with writer.open("w", encoding="utf-8") as f:
            f.write("v2")
        with writer.open("w", encoding="utf-8") as f:
            f.write("v3")

        assert target.read_text() == "v3"

        bak1 = target.with_suffix(target.suffix + ".bak1")
        bak2 = target.with_suffix(target.suffix + ".bak2")
        bak3 = target.with_suffix(target.suffix + ".bak3")

        assert bak1.exists()
        assert bak1.read_text() == "v2"
        assert bak2.exists()
        assert bak2.read_text() == "v1"
        assert not bak3.exists()

    def test_rotation_exact_capacity(self, tmp_path: Path):
        """写 N+1 次后最旧备份刚好被挤出。"""
        target = tmp_path / "x.txt"
        writer = SafeFileWriter(target, num_backups=1)

        with writer.open("w", encoding="utf-8") as f:
            f.write("a")
        with writer.open("w", encoding="utf-8") as f:
            f.write("b")

        assert target.read_text() == "b"
        bak1 = target.with_suffix(target.suffix + ".bak1")
        assert bak1.exists()
        assert bak1.read_text() == "a"
        bak2 = target.with_suffix(target.suffix + ".bak2")
        assert not bak2.exists()


class TestNoBackups:
    """num_backups=0：原子写入但不产生任何 .bak* 文件。"""

    def test_no_bak_files_created(self, tmp_path: Path):
        target = tmp_path / "f.txt"
        writer = SafeFileWriter(target, num_backups=0)

        target.write_text("first")
        with writer.open("w", encoding="utf-8") as f:
            f.write("second")

        assert target.read_text() == "second"
        bak_files = list(tmp_path.glob("*.bak*"))
        assert bak_files == []


class TestFirstWriteNoBackup:
    """目标文件不存在时首次写入 (num_backups>0)：不备份，直接成功写入，无 .bak*。"""

    def test_first_write_creates_only_target(self, tmp_path: Path):
        target = tmp_path / "new.txt"
        assert not target.exists()

        writer = SafeFileWriter(target, num_backups=2)
        with writer.open("w", encoding="utf-8") as f:
            f.write("first")

        assert target.read_text() == "first"
        bak_files = list(tmp_path.glob("*.bak*"))
        assert bak_files == []
        assert list(tmp_path.glob("*.tmp")) == []
