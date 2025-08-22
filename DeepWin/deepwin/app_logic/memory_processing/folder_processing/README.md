# Folder Processing Package

## 简介

文件夹处理包,用于管理和监控文件夹变化,支持文件的自动处理和分类。

## 主要功能

### 1. 文件夹监控

```python
from folder_processing.monitor import FolderMonitor

# 初始化监控器
monitor = FolderMonitor("path/to/watch")

# 开始监控
monitor.start()

# 停止监控
monitor.stop()
```

### 2. 文件处理

```python
from folder_processing.processor import FileProcessor

processor = FileProcessor()

# 处理单个文件
result = processor.process_file("path/to/file")

# 批量处理文件
results = processor.process_folder("path/to/folder")
```

### 3. 文件分类

```python
# 按类型分类
processor.classify_by_type("path/to/folder")

# 按日期分类
processor.classify_by_date("path/to/folder")
```

## 事件回调

```python
def on_file_created(event):
    print(f"File created: {event.src_path}")

def on_file_modified(event):
    print(f"File modified: {event.src_path}")

monitor.set_callbacks(
    on_created=on_file_created,
    on_modified=on_file_modified
)
```

## 配置说明

```json
{
  "monitor": {
    "patterns": ["*.jpg", "*.png", "*.txt"],
    "recursive": true,
    "ignore_patterns": ["*.tmp"]
  },
  "processor": {
    "max_size": 10485760,
    "allowed_types": ["image", "text", "video"]
  }
}
```

## 注意事项

1. 确保有足够的权限访问目标文件夹
2. 大量文件处理时注意内存使用
3. 建议使用异步处理避免阻塞
