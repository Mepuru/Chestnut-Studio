# 字幕编辑对话框

> `chestnut_studio/ui/dialogs/edit_subtitle_dialog.py`
> `EditSubtitleDialog(QDialog)` — 字幕区间编辑对话框。

---

## 职责

- 编辑字幕的起止时间
- 可视化调整字幕区间
- 提供确认和取消操作

---

## 信号

| 信号 | 参数 | 说明 |
|------|------|------|
| `accepted` | 无 | 用户确认 |
| `rejected` | 无 | 用户取消 |

---

## 布局

```
┌─ 编辑字幕 ─────────────────────────────────────┐
│                                                 │
│  开始时间:  [00:01.000]  [▲] [▼]               │
│                                                 │
│  结束时间:  [00:03.000]  [▲] [▼]               │
│                                                 │
│  持续时间:  2.000s                              │
│                                                 │
│              [取消]  [确认]                      │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## 公有方法

| 方法 | 参数 | 返回 | 说明 |
|------|------|------|------|
| `get_start_ms()` | 无 | `int` | 获取开始时间（毫秒） |
| `get_end_ms()` | 无 | `int` | 获取结束时间（毫秒） |
| `set_start_ms(ms)` | `int` | 无 | 设置开始时间 |
| `set_end_ms(ms)` | `int` | 无 | 设置结束时间 |

---

## 用法示例

```python
from chestnut_studio.ui.dialogs.edit_subtitle_dialog import EditSubtitleDialog

# 创建对话框
dialog = EditSubtitleDialog(col=1, start_ms=1000, end_ms=3000)

# 连接信号
dialog.accepted.connect(self.on_dialog_accepted)
dialog.rejected.connect(self.on_dialog_rejected)

# 显示对话框
result = dialog.exec()

# 处理结果
if result == QDialog.Accepted:
    new_start = dialog.get_start_ms()
    new_end = dialog.get_end_ms()
    print(f"新区间: {new_start} - {new_end}")
```

---

## 初始化参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `col` | `int` | 列号（1-4） |
| `start_ms` | `int` | 开始时间（毫秒） |
| `end_ms` | `int` | 结束时间（毫秒） |
| `parent` | `QWidget` | 父窗口 |

---

## 时间编辑

### 时间格式

- 显示格式：`MM:SS.mmm`
- 输入格式：`MM:SS.mmm` 或 `MM:SS`
- 内部存储：毫秒

### 调整方式

- 直接输入时间
- 点击上/下箭头微调
- 键盘上下箭头微调

### 微调步长

- 毫秒位：±1ms
- 秒位：±1s
- 分钟位：±1min

---

## 数据验证

### 时间范围

- 开始时间 >= 0
- 结束时间 > 开始时间
- 持续时间 > 0

### 错误处理

- 输入格式错误：显示错误提示
- 时间范围错误：显示错误提示
- 自动修正无效输入

---

## 注意事项

### 模态对话框

- 对话框为模态，阻塞父窗口交互
- 用户必须确认或取消才能继续操作
- 关闭对话框后自动释放资源

### 数据同步

- 对话框关闭前不修改原始数据
- 确认后返回新数据，由调用者决定是否应用
- 取消后不返回数据

### 焦点管理

- 对话框获得焦点时禁用父窗口
- 对话框关闭时恢复父窗口焦点
- 避免焦点丢失导致的交互问题

---

## 依赖

- PySide6: `QDialog`, `QWidget`, `QVBoxLayout`, `QTimeEdit`, `QPushButton`
- chestnut_studio.utils.time_utils: `ms_to_time_str`, `time_str_to_ms`
