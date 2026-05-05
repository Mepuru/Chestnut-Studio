# M11 — 字幕数据结构

> `src/core/subtitle.py`　｜　Phase 3　｜　纯逻辑，无 UI 依赖

---

## 职责

- 字幕数据的存储和操作
- 添加/删除/修改字幕条
- 合并/拆分/切割字幕条
- 叠轴检测
- 撤销/重做栈管理

---

## 核心数据结构

```python
# 字幕字典
# key: 列号 (0-4)
# value: {start_ms: [duration_ms, "text"], ...}
SubtitleDict = dict[int, dict[int, list]]
```

示例：
```python
{
    0: {
        15200: [3200, "你好"],
        22000: [1800, "谢谢"],
    },
    1: {},
    2: {},
    3: {},
    4: {},
}
```

---

## 类设计

```python
class SubtitleManager:
    """字幕管理器"""
    
    def __init__(self):
        self._data: SubtitleDict = {0: {}, 1: {}, 2: {}, 3: {}, 4: {}}
        self._undo_stack: list[SubtitleDict] = []
        self._undo_index: int = -1
    
    @property
    def data(self) -> SubtitleDict:
        return self._data
    
    def get(self, col: int, start: int) -> tuple[int, str] | None:
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
    
    def split(self, col: int, time_point: int):
        """在指定时间点切割字幕条"""
        for start, (delta, text) in list(self._data[col].items()):
            end = start + delta
            if start < time_point < end:
                self._data[col][start] = [time_point - start, text]
                self._data[col][time_point] = [end - time_point, text]
                return True
        return False
    
    def break_to_rows(self, col: int, time_points: list[int], interval: float):
        """将字幕拆分成每行独立条"""
        for tp in time_points:
            for start, (delta, text) in list(self._data[col].items()):
                if start <= tp < start + delta:
                    self._data[col][int(tp)] = [int(interval), text]
    
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
        import copy
        state = copy.deepcopy(self._data)
        self._undo_stack = self._undo_stack[:self._undo_index + 1]
        self._undo_stack.append(state)
        self._undo_index += 1
        if len(self._undo_stack) > 100:
            self._undo_stack.pop(0)
            self._undo_index -= 1
    
    def undo(self) -> bool:
        """撤销，返回是否成功"""
        if self._undo_index > 0:
            self._undo_index -= 1
            self._data = copy.deepcopy(self._undo_stack[self._undo_index])
            return True
        return False
    
    def redo(self) -> bool:
        """重做，返回是否成功"""
        if self._undo_index < len(self._undo_stack) - 1:
            self._undo_index += 1
            self._data = copy.deepcopy(self._undo_stack[self._undo_index])
            return True
        return False
    
    def clear(self, col: int):
        """清空指定列"""
        self._data[col] = {}
    
    def clear_all(self):
        """清空所有"""
        self._data = {0: {}, 1: {}, 2: {}, 3: {}, 4: {}}
```

---

## 测试用例

```python
class TestSubtitleManager:
    def test_set_and_get(self):
        mgr = SubtitleManager()
        mgr.set(0, 1000, 2000, "你好")
        assert mgr.get(0, 1000) == [2000, "你好"]
    
    def test_delete(self):
        mgr = SubtitleManager()
        mgr.set(0, 1000, 2000, "你好")
        mgr.delete(0, 1000)
        assert mgr.get(0, 1000) is None
    
    def test_merge(self):
        mgr = SubtitleManager()
        mgr.set(0, 1000, 1000, "你")
        mgr.set(0, 2000, 1000, "好")
        mgr.merge(0, 1000, 3000, "你好")
        assert mgr.get(0, 1000) == [2000, "你好"]
    
    def test_split(self):
        mgr = SubtitleManager()
        mgr.set(0, 1000, 2000, "你好")
        mgr.split(0, 2000)
        assert mgr.get(0, 1000) == [1000, "你好"]
        assert mgr.get(0, 2000) == [1000, "你好"]
    
    def test_undo_redo(self):
        mgr = SubtitleManager()
        mgr.push_undo()
        mgr.set(0, 1000, 2000, "你好")
        mgr.push_undo()
        mgr.set(0, 3000, 1000, "世界")
        mgr.undo()
        assert mgr.get(0, 3000) is None
        mgr.redo()
        assert mgr.get(0, 3000) == [1000, "世界"]
```

---

## 依赖

| 依赖 | 用途 |
|------|------|
| copy (标准库) | 深拷贝 |
| 无外部依赖 | 纯逻辑模块 |
