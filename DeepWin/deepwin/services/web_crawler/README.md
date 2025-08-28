# DeepWin 爬虫服务

## 概述

DeepWin 爬虫服务提供了多种网络爬虫功能，支持图片批量下载和分类存储。该服务位于`services/web_crawler/`目录下，为整个 DeepWin 系统提供数据采集能力。

## 目录结构

```
web_crawler/
├── __init__.py                           # 包初始化文件
├── requirements.txt                      # 依赖包列表
├── README.md                            # 本文档
├── unsplash_api_crawler.py              # Unsplash API 爬虫类
├── baidu_crawler.py                     # 百度图片爬虫类
├── crawler_manager.py                   # 爬虫管理器
├── demo.py                              # 使用示例和演示
├── config_example.py                    # 配置示例文件
└── logs/                                # 日志目录
```

## 功能特性

### 1. 多爬虫支持

- **Unsplash API 爬虫**: 使用官方 API，获取高质量图片
- **百度图片爬虫**: 支持中文关键词搜索，图片数量丰富
- **爬虫管理器**: 统一管理所有爬虫，提供统一接口

### 2. 智能存储管理

- **分类存储**: 按关键词自动创建子目录
- **统一输出**: 使用项目统一的输出目录 `output/crawler_images/`
- **历史管理**: 支持查看下载历史和清理旧文件

### 3. 配置管理

- **环境变量**: 支持从环境变量读取 API 密钥
- **配置管理器**: 与项目统一配置管理器集成
- **日志管理**: 与项目统一日志管理器集成
- **统一配置**: 通过 `config.json` 统一管理所有爬虫配置

### 4. 批量处理

- **多关键词**: 支持同时处理多个搜索关键词
- **多爬虫**: 支持使用多个爬虫同时工作
- **并发下载**: 支持多线程并发下载

### 5. 异步执行

- **任务调度器集成**: 与 DeepWin 的 `TaskScheduler` 集成
- **非阻塞操作**: 支持异步执行爬虫任务
- **回调机制**: 任务完成和失败的回调处理

## 使用方法

### 1. 安装依赖

```bash
cd DeepWin/deepwin/services/web_crawler
pip install -r requirements.txt
```

### 2. 环境配置

#### 设置 Unsplash API 密钥

```bash
# 在环境变量中设置
export UNSPLASH_ACCESS_KEY="your_api_key_here"

# 或者在 .env 文件中设置
UNSPLASH_ACCESS_KEY=your_api_key_here
```

#### 配置管理器设置

爬虫服务现在完全集成到项目的统一配置管理系统中。所有配置都在 `config.json` 中管理：

```json
{
  "web_crawler": {
    "output_dir": "output/crawler_images",
    "unsplash": {
      "access_key": "your_api_key_here",
      "max_workers": 5,
      "per_page": 10,
      "delay": 1.0,
      "enabled": true
    },
    "baidu": {
      "time_sleep": 0.1,
      "per_page": 30,
      "timeout": 10,
      "enabled": true
    },
    "global": {
      "max_concurrent_downloads": 3,
      "default_pages": 1,
      "cleanup_empty_files": true,
      "retry_failed_downloads": true,
      "max_retries": 3
    }
  }
}
```

### 3. 基础使用

#### 使用 Unsplash API 爬虫

```python
from deepwin.services.web_crawler import UnsplashApiCrawler
from deepwin.data_management.log_manager import LogManager
from deepwin.config.config_manager import ConfigManager

# 创建管理器实例
log_manager = LogManager()
config_manager = ConfigManager(log_manager=log_manager)

# 创建爬虫实例
crawler = UnsplashApiCrawler(log_manager=log_manager, config_manager=config_manager)

# 批量下载图片
result = crawler.batch_download(
    query="cat",
    pages=2
)

print(f"下载完成: {result['downloaded_images']}/{result['total_images']}")
```

#### 使用百度爬虫

```python
from deepwin.services.web_crawler import BaiduCrawler

# 创建爬虫实例
crawler = BaiduCrawler(log_manager=log_manager, config_manager=config_manager)

# 批量下载多个关键词
queries = ["cat", "dog", "bird"]
results = crawler.batch_download(queries, total_pages=1)

print(f"处理完成: {results['summary']['success_count']}/{results['summary']['total_queries']}")
```

#### 使用爬虫管理器（推荐）

```python
from deepwin.services.web_crawler import CrawlerManager

# 创建管理器实例
manager = CrawlerManager(log_manager=log_manager, config_manager=config_manager)

# 使用指定爬虫下载
result = manager.download_images('unsplash', 'cat', 2)

# 批量下载多个关键词
queries = ["cat", "dog", "bird"]
results = manager.batch_download_multiple_queries('unsplash', queries, 1)

# 使用多个爬虫同时工作
multi_results = manager.download_with_multiple_crawlers(queries, 1)
```

### 4. 高级功能

#### 查看爬虫状态

```python
# 获取所有爬虫状态
status = manager.get_crawler_status()
print(f"可用爬虫: {manager.list_crawlers()}")

# 获取爬虫配置
config = manager.get_crawler_config('unsplash')
print(f"Unsplash配置: {config}")
```

#### 管理下载历史

```python
# 查看下载历史
history = manager.get_download_history()
print(f"总关键词数: {history['total_keywords']}")
print(f"总图片数: {history['total_images']}")

# 清理旧文件
cleanup_result = manager.cleanup_old_downloads(days=30)
print(f"清理了 {cleanup_result['cleaned_dirs']} 个目录")
```

#### 更新爬虫配置

```python
# 更新 Unsplash 爬虫配置
manager.update_crawler_config('unsplash',
                             max_workers=10,
                             delay=2.0)

# 更新百度爬虫配置
manager.update_crawler_config('baidu',
                             time_sleep=0.2)
```

## 输出目录结构

爬取的图片会按关键词分类存储在以下目录结构中：

```
DeepWin/output/crawler_images/
├── cat/                    # 关键词 "cat" 的图片
│   ├── img_1.jpg
│   ├── img_2.jpg
│   └── ...
├── dog/                    # 关键词 "dog" 的图片
│   ├── img_1.jpg
│   ├── img_2.jpg
│   └── ...
└── bird/                   # 关键词 "bird" 的图片
    ├── img_1.jpg
    ├── img_2.jpg
    └── ...
```

## 配置选项

### 全局配置

```json
{
  "web_crawler": {
    "output_dir": "output/crawler_images",
    "global": {
      "max_concurrent_downloads": 3,
      "default_pages": 1,
      "cleanup_empty_files": true,
      "retry_failed_downloads": true,
      "max_retries": 3
    }
  }
}
```

### Unsplash API 爬虫配置

```json
{
  "web_crawler": {
    "unsplash": {
      "access_key": "your_api_key_here",
      "max_workers": 5,
      "per_page": 10,
      "delay": 1.0,
      "enabled": true
    }
  }
}
```

### 百度爬虫配置

```json
{
  "web_crawler": {
    "baidu": {
      "time_sleep": 0.1,
      "per_page": 30,
      "timeout": 10,
      "enabled": true
    }
  }
}
```

## 与 DeepWin 系统集成

### 1. 在 services/**init**.py 中导出

```python
from .web_crawler import CrawlerManager, UnsplashApiCrawler, BaiduCrawler

__all__ = [
    # ... 其他导出
    'CrawlerManager',
    'UnsplashApiCrawler',
    'BaiduCrawler',
]
```

### 2. 在协调器中使用

```python
from deepwin.services.web_crawler import CrawlerManager

class Coordinator:
    def __init__(self):
        self.crawler_manager = CrawlerManager(
            log_manager=self.log_manager,
            config_manager=self.config_manager
        )

    def start_application(self):
        # 使用任务调度器异步执行爬虫任务
        crawler_task_id = self.task_scheduler.add_delayed_task(
            task_func=self.test_crawler,
            delay_ms=1000,
            task_name="爬虫功能测试"
        )

        # 连接任务完成和失败信号
        self.task_scheduler.task_completed.connect(self._on_crawler_task_completed)
        self.task_scheduler.task_failed.connect(self._on_crawler_task_failed)

    def test_crawler(self):
        # 测试爬虫功能
        result = self.crawler_manager.download_images('unsplash', 'starry sky', 1)
        return result
```

### 3. 在处理器中使用

```python
from deepwin.app_logic.core_manager.base_handler import BaseHandler

class WebCrawlerHandler(BaseHandler):
    def __init__(self, parent=None):
        super().__init__(parent)

    def download_images(self, crawler_type, query, pages=1):
        if self.crawler_manager:
            return self.crawler_manager.download_images(crawler_type, query, pages)
        return {"error": "爬虫管理器未初始化"}
```

## 演示和测试

### 运行演示

```bash
cd DeepWin/deepwin/services/web_crawler

# 运行完整演示
python demo.py

# 运行特定组件演示
python demo.py --component=baidu
python demo.py --component=unsplash
python demo.py --component=manager
python demo.py --component=integration
python demo.py --component=batch
```

### 测试单个爬虫

```bash
# 测试 Unsplash 爬虫
python -c "from unsplash_api_crawler import UnsplashApiCrawler; print('导入成功')"

# 测试百度爬虫
python -c "from baidu_crawler import BaiduCrawler; print('导入成功')"

# 测试爬虫管理器
python -c "from crawler_manager import CrawlerManager; print('导入成功')"
```

## 最佳实践

### 1. 使用爬虫管理器

- 推荐使用 `CrawlerManager` 而不是直接使用爬虫类
- 管理器提供统一的接口和错误处理
- 自动管理配置和日志

### 2. 合理设置延迟

- Unsplash API: 建议延迟 1-2 秒
- 百度爬虫: 建议延迟 0.1-0.5 秒
- 通过配置文件统一管理延迟设置

### 3. 批量处理

- 使用批量下载功能减少重复代码
- 合理设置并发数量避免被限制
- 利用多爬虫并行处理提高效率

### 4. 错误处理

- 检查返回结果中的错误信息
- 实现重试机制处理临时错误
- 使用统一的日志管理器记录错误

### 5. 异步执行

- 在 UI 应用中使用 `TaskScheduler` 异步执行爬虫任务
- 避免阻塞主线程
- 使用信号机制处理任务完成和失败

## 故障排除

### 常见问题

#### 1. Unsplash API 密钥问题

```bash
# 检查环境变量
echo $UNSPLASH_ACCESS_KEY

# 或在代码中检查
import os
print(os.getenv("UNSPLASH_ACCESS_KEY"))

# 检查配置文件
from deepwin.config.config_manager import ConfigManager
config = ConfigManager()
print(config.get("web_crawler.unsplash.access_key"))
```

#### 2. 权限问题

```bash
# 确保输出目录有写权限
chmod 755 output/crawler_images
```

#### 3. 网络问题

- 检查网络连接
- 确认防火墙设置
- 尝试使用代理

#### 4. 配置问题

```python
# 检查爬虫配置
manager = CrawlerManager(log_manager, config_manager)
config = manager.get_global_config()
print(f"全局配置: {config}")
```

### 调试技巧

#### 启用详细日志

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 或使用项目的日志管理器
log_manager = LogManager()
log_manager.set_level(logging.DEBUG)
```

#### 检查爬虫状态

```python
status = manager.get_crawler_status()
print(status)

# 检查特定爬虫
unsplash_status = manager.get_crawler_status()['unsplash']
print(f"Unsplash状态: {unsplash_status}")
```

## 扩展开发

### 1. 添加新的爬虫类型

继承基础爬虫类或实现特定接口：

```python
class CustomCrawler:
    def __init__(self, log_manager=None, config_manager=None):
        self.logger = log_manager.get_logger(__name__) if log_manager else logging.getLogger(__name__)
        self.config_manager = config_manager
        # 初始化逻辑
        pass

    def download_images(self, query, pages=1):
        # 实现下载逻辑
        pass

    def get_crawler_config(self):
        # 返回爬虫配置
        pass

    def update_crawler_config(self, **kwargs):
        # 更新爬虫配置
        pass
```

### 2. 集成到管理器

在 `CrawlerManager` 中添加新爬虫：

```python
def _init_crawlers(self):
    # ... 现有代码 ...

    # 添加新爬虫
    self.crawlers['custom'] = CustomCrawler(
        log_manager=self.logger.parent,
        config_manager=self.config_manager
    )
```

### 3. 添加新的配置选项

在 `config.json` 中添加新爬虫的配置：

```json
{
  "web_crawler": {
    "custom": {
      "enabled": true,
      "timeout": 30,
      "max_retries": 5
    }
  }
}
```

## 注意事项

1. **API 限制**: 注意 Unsplash API 的请求频率限制
2. **法律合规**: 确保爬取行为符合目标网站的使用条款
3. **资源管理**: 合理控制并发数量和下载频率
4. **存储空间**: 注意图片文件会占用大量存储空间
5. **配置管理**: 所有配置都通过统一的配置管理器管理
6. **异步执行**: 在 UI 应用中避免阻塞主线程

## 技术支持

如果遇到问题，请：

1. 检查日志输出
2. 验证环境配置
3. 确认依赖包版本
4. 查看演示代码示例
5. 检查配置文件设置
6. 验证与协调器的集成

---

**版本**: 2.0.0  
**更新日期**: 2025 年 8 月 28 日
**维护者**: DeepWin Team  
**集成状态**: 已完全集成到 DeepWin 协调器系统
