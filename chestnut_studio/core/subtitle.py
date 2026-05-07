"""字幕数据结构与操作"""

import copy

# 字幕字典类型
# key: 列号 (1-4)
# value: {start_ms: [duration_ms, "text"], ...}
SubtitleDict = dict[int, dict[int, list]]


class SubtitleManager:
    """字幕管理器"""

    MAX_UNDO = 100

    def __init__(self):
        self._data: SubtitleDict = {1: {}, 2: {}, 3: {}, 4: {}}
        self._undo_stack: list[SubtitleDict] = []
        self._undo_index: int = -1
        self._in_undo_mode: bool = False

    @property
    def data(self) -> SubtitleDict:
        return self._data

    def get(self, col: int, start: int) -> list | None:
        """获取字幕条"""
        return self._data[col].get(start)

    def set(self, col: int, start: int, duration: int, text: str):
        """设置字幕条"""
        self._data[col][start] = [duration, text]

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
        self._data[col][start] = [end - start, text]

    def split(self, col: int, time_point: int) -> bool:
        """在指定时间点切割字幕条"""
        for start, (delta, text) in list(self._data[col].items()):
            end = start + delta
            if start < time_point < end:
                self._data[col][start] = [time_point - start, text]
                self._data[col][time_point] = [end - time_point, text]
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

    def push_undo(self):
        """保存当前状态到撤销栈"""
        state = copy.deepcopy(self._data)
        self._undo_stack = self._undo_stack[: self._undo_index + 1]
        self._undo_stack.append(state)
        self._undo_index += 1
        if len(self._undo_stack) > self.MAX_UNDO:
            self._undo_stack.pop(0)
            self._undo_index -= 1

    def undo(self) -> bool:
        """撤销，返回是否成功"""
        if self._undo_index > 0:
            # 如果不在撤销模式，保存当前状态以便重做
            if not self._in_undo_mode:
                self._redo_state = copy.deepcopy(self._data)
                self._in_undo_mode = True
            self._undo_index -= 1
            self._data = copy.deepcopy(self._undo_stack[self._undo_index])
            return True
        return False

    def redo(self) -> bool:
        """重做，返回是否成功"""
        if self._in_undo_mode:
            self._data = copy.deepcopy(self._redo_state)
            self._in_undo_mode = False
            return True
        return False

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
                    self._data[col][int(tp)] = [int(interval), text]

    def clear(self, col: int):
        """清空指定列"""
        self._data[col] = {}

    def clear_all(self):
        """清空所有"""
        self._data = {1: {}, 2: {}, 3: {}, 4: {}}
