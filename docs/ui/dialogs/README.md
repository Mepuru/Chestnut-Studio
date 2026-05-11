# 弹窗组件

> `chestnut_studio/ui/dialogs/` 下各弹窗组件的接口和设计说明。
> 弹窗组件用于显示对话框和提示信息。

---

## 模块概览

| 模块 | 文件 | 职责 |
|------|------|------|
| [调试控制台](debug_console.md) | `debug_console.py` | 日志输出、级别过滤、颜色区分 |
| [字幕编辑对话框](edit_subtitle_dialog.md) | `edit_subtitle_dialog.py` | 字幕区间编辑 |

---

## 设计原则

### 1. 模态对话框

弹窗组件通常为模态对话框：
- 阻塞父窗口交互
- 用户必须关闭对话框才能继续操作
- 适用于需要用户确认或输入的场景

### 2. 信号通信

弹窗通过信号返回结果：
- `accepted` - 用户确认
- `rejected` - 用户取消
- 自定义信号 - 返回特定数据

### 3. 布局规范

弹窗布局应简洁明了：
- 标题栏显示对话框标题
- 内容区域显示主要信息
- 按钮区域显示操作按钮

---

## 使用示例

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
```

---

## 注意事项

### 内存管理

- 对话框使用后自动释放
- 避免创建过多对话框实例
- 使用 `deleteLater()` 确保资源释放

### 焦点管理

- 对话框获得焦点时禁用父窗口
- 对话框关闭时恢复父窗口焦点
- 避免焦点丢失导致的交互问题

---

## 依赖

- PySide6: `QDialog`, `QWidget`, `QVBoxLayout`
