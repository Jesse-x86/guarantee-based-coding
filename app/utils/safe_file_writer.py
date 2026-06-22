# REQUIREMENTS
# None, raw python should have all libs required
# From https://github.com/Jesse-x86/devkit/blob/master/file_operations/safe_file_writer.py
import logging
import os
import shutil
from pathlib import Path


class SafeFileWriter:
    """
    一个安全的文件写入器，通过上下文管理器（with语句）提供原子写入和自动备份功能。

    功能特性:
    1.  **原子性**: 先写入到一个临时文件，只有在with代码块成功执行完毕后，
        才会用新内容覆盖原文件，有效防止因写入中断导致的文件损坏。
    2.  **自动备份**: 在覆盖原文件之前，会自动将旧文件备份。
    3.  **备份管理**: 自动维护指定数量的备份文件（如 .bak1, .bak2 ...），
        并删除更早的备份。
    4.  **自动回滚**: 如果with代码块中发生任何异常，临时文件将被删除，
        原始文件和备份文件将保持不变，实现自动回滚。
    5.  **灵活写入**: 调用方在with块内可以获得一个标准的文件句柄，可以像操作
        普通文件一样进行写入（write, writelines, print(file=f)等），
        完全控制写入的内容和方式。

    使用示例:
        writer = SafeFileWriter('my_data.json', num_backups=3)
        try:
            with writer.open(mode='w', encoding='utf-8') as f:
                # f 是一个真正的文件句柄，可以自由写入
                import json
                json.dump({'key': 'new value'}, f, indent=4)
                # 假设这里发生错误
                # raise ValueError("写入过程中发生错误")
        except Exception as e:
            print(f"写入失败: {e}")

    # 如果成功，'my_data.json' 会被更新，旧文件变为 'my_data.json.bak1'
    # 如果失败，'my_data.json' 保持原样，不会产生不完整的文件。
    """

    def __init__(self, filepath: str | Path, num_backups: int = 0):
        """
        初始化SafeFileWriter。

        Args:
            filepath (str | Path): 目标文件的完整路径。
            num_backups (int, optional): 需要保留的最大备份数量。默认为 0。
                                         如果为0，则不创建备份，但仍保证原子写入。
        """
        self._mode = None
        self._open_kwargs = None
        self.filepath = Path(filepath)
        self.num_backups = max(0, num_backups)
        self._temp_path = None
        self._file_handle = None
        self._logger = logging.getLogger("SafeFileWriter")

    def _log(self, msg: str):
        self._logger.debug(msg)

    def _rotate_backups(self):
        """管理和轮转备份文件。"""
        if not self.filepath.exists() or self.num_backups == 0:
            return

        # 1. 删除最旧的备份 (如果存在)
        oldest_bak = self.filepath.with_suffix(f"{self.filepath.suffix}.bak{self.num_backups}")
        if oldest_bak.exists():
            oldest_bak.unlink()

        # 2. 将现有备份序号+1
        # 从后往前重命名，避免覆盖
        for i in range(self.num_backups - 1, 0, -1):
            src_bak = self.filepath.with_suffix(f"{self.filepath.suffix}.bak{i}")
            dst_bak = self.filepath.with_suffix(f"{self.filepath.suffix}.bak{i + 1}")
            if src_bak.exists():
                shutil.move(str(src_bak), str(dst_bak))

        # 3. 将当前文件创建为第一个备份
        first_bak = self.filepath.with_suffix(f"{self.filepath.suffix}.bak1")
        shutil.move(str(self.filepath), str(first_bak))
        self._log(f"备份: {self.filepath.name} -> {first_bak.name}")

    def open(self, mode='w', **kwargs):
        """
        以上下文管理器的方式打开文件准备写入。

        Args:
            mode (str, optional): 文件打开模式，推荐使用 'w' (文本) 或 'wb' (二进制)。
                                  追加模式 'a' 在此逻辑下意义不大。默认为 'w'。
            **kwargs: 传递给内建 open() 函数的其他参数, 如 encoding, errors等。

        Returns:
            一个上下文管理器对象。
        """
        self._mode = mode
        self._open_kwargs = kwargs
        return self

    def __enter__(self):
        """上下文管理器的进入方法，准备临时文件。"""
        # 创建一个唯一的临时文件
        self._temp_path = self.filepath.with_suffix(f"{self.filepath.suffix}.{os.urandom(6).hex()}.tmp")

        # 打开临时文件用于写入，并将文件句柄返回给 `with ... as f:`
        self._file_handle = open(self._temp_path, self._mode, **self._open_kwargs)
        return self._file_handle

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        上下文管理器的退出方法，处理提交或回滚。

        exc_type, exc_val, exc_tb: 如果with块内有异常，这些是异常信息，否则为None。
        """
        # 1. 必须确保文件句柄被关闭
        if self._file_handle and not self._file_handle.closed:
            self._file_handle.close()

        # 2. 检查with块是否成功执行
        if exc_type is None:
            # 成功: 执行备份和替换
            try:
                self._log(f"写入成功，准备更新文件: {self.filepath.name}")
                # a. 轮转备份
                if self.num_backups > 0:
                    self._rotate_backups()
                # b. 将临时文件重命名为目标文件 (原子操作)
                shutil.move(str(self._temp_path), str(self.filepath))
                self._log(f"文件已更新: {self.filepath.name}")
            except Exception as e:
                self._log(f"错误：在提交文件时发生意外: {e}")
                # 如果提交阶段也失败了，尝试清理临时文件
                if self._temp_path.exists():
                    self._temp_path.unlink()
                # 让外部知道提交失败了
                raise
        else:
            # 失败: 清理临时文件，不触碰原文件和备份
            self._log(f"写入失败，正在回滚...")
            if self._temp_path.exists():
                self._temp_path.unlink()
                self._log(f"已删除临时文件: {self._temp_path.name}")
            # 异常会由Python自动重新抛出，调用方可以捕获它