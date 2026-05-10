"""字幕数据结构与操作"""

import copy
from typing import NamedTuple


class SubtitleEntry(NamedTuple):
    """字幕条目

    Attributes:
        duration_ms: 持续时间（毫秒）
        text: 字幕文本
    """

    duration_ms: int
    text: str


# 字幕字典类型
# key: 列号 (1-4)
# value: {start_ms: SubtitleEntry(duration_ms, text), ...}
SubtitleDict = dict[int, dict[int, SubtitleEntry]]


class SubtitleManager:
    """字幕管理器"""

    def __init__(self):
        self._data: SubtitleDict = {1: {}, 2: {}, 3: {}, 4: {}}

    @property
    def data(self) -> SubtitleDict:
        return self._data

    def get(self, col: int, start: int) -> SubtitleEntry | None:
        """获取字幕条"""
        return self._data[col].get(start)

    def set(self, col: int, start: int, duration: int, text: str):
        """设置字幕条"""
        self._data[col][start] = SubtitleEntry(duration, text)

    def delete(self, col: int, start: int):
        """删除字幕条"""
        if start in self._data[col]:
            del self._data[col][start]

    def delete_range(self, col: int, start: int, end: int):
        """删除指定范围内的所有字幕条"""
        to_delete = []
        for s, (d, _) in self._data[col].items():
            e = s + d
            if s < end and e > start:
                to_delete.append(s)
        for s in to_delete:
            del self._data[col][s]

    def merge(self, col: int, start: int, end: int, text: str):
        """合并范围内的字幕为一条"""
        self.delete_range(col, start, end)
        self._data[col][start] = SubtitleEntry(end - start, text)

    def split(self, col: int, time_point: int) -> bool:
        """在指定时间点切割字幕条"""
        for start, (delta, text) in list(self._data[col].items()):
            end = start + delta
            if start < time_point < end:
                self._data[col][start] = SubtitleEntry(time_point - start, text)
                self._data[col][time_point] = SubtitleEntry(end - time_point, text)
                return True
        return False

    def check_overlap(self, col: int, start: int, end: int, interval: float) -> int:
        """检测叠轴

        Returns:
            0: 有重叠，阻止
            1: 安全
            2: 有重叠但可调整
        """
        for s, (d, _) in self._data[col].items():
            e = s + d
            if start < e and end > s:
                if start >= e - interval:
                    return 2
                return 0
        return 1

    def break_to_rows(self, col: int, time_points: list[int], interval: float):
        """将字幕拆分成每行独立条

        Args:
            col: 列号
            time_points: 时间点列表
            interval: 间隔 (ms)
        """
        for tp in time_points:
            for start, (delta, text) in list(self._data[col].items()):
                if start <= tp < start + delta:
                    self._data[col][int(tp)] = SubtitleEntry(int(interval), text)

    def clear(self, col: int):
        """清空指定列"""
        self._data[col] = {}

    def clear_all(self):
        """清空所有"""
        self._data = {1: {}, 2: {}, 3: {}, 4: {}}

    def ensure_track(self, col: int):
        """确保指定轨道存在，如果不存在则创建"""
        if col not in self._data:
            self._data[col] = {}

    def get_max_track(self) -> int:
        """获取当前最大轨道号"""
        if not self._data:
            return 0
        return max(self._data.keys())

    def add_track(self, col: int) -> bool:
        """添加新轨道

        Args:
            col: 轨道号

        Returns:
            是否成功添加（如果已存在则返回False）
        """
        if col in self._data:
            return False
        self._data[col] = {}
        return True

    def copy_track(self, source_col: int, target_col: int) -> bool:
        """复制轨道数据到另一个轨道

        Args:
            source_col: 源轨道号 (1-4)
            target_col: 目标轨道号 (1-4)

        Returns:
            是否成功复制
        """
        if source_col not in self._data or target_col not in self._data:
            return False
        if source_col == target_col:
            return False

        # 深拷贝源轨道数据到目标轨道
        self._data[target_col] = copy.deepcopy(self._data[source_col])
        return True
