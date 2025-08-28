#!/usr/bin/env python3
"""
爬虫处理器
处理爬虫相关的业务逻辑和UI请求
"""

from PySide6.QtCore import Signal
from deepwin.app_logic.core_manager.base_handler import BaseHandler
from typing import Dict, List, Optional


class WebCrawlerHandler(BaseHandler):
    """
    爬虫处理器
    处理爬虫相关的业务逻辑，作为UI和爬虫管理器之间的桥梁
    """
    
    # 定义信号
    crawler_status_changed = Signal(str, dict)  # 爬虫状态变化信号
    download_progress = Signal(str, int, int)   # 下载进度信号 (crawler_type, current, total)
    download_completed = Signal(str, dict)      # 下载完成信号 (crawler_type, result)
    download_error = Signal(str, str)           # 下载错误信号 (crawler_type, error_message)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger.info("WebCrawlerHandler: 初始化爬虫处理器")
    
    def _validate_dependencies(self):
        """验证必需的依赖项"""
        if not self.crawler_manager:
            raise ValueError("爬虫管理器未初始化")
        if not self.logger:
            raise ValueError("日志管理器未初始化")
        if not self.config_manager:
            raise ValueError("配置管理器未初始化")
    
    def _connect_signals(self):
        """连接信号和槽"""
        # 这里可以连接爬虫管理器的信号
        pass
    
    def get_available_crawlers(self) -> List[str]:
        """获取可用的爬虫类型"""
        try:
            return self.crawler_manager.list_crawlers()
        except Exception as e:
            self.logger.error(f"获取可用爬虫失败: {e}")
            return []
    
    def get_crawler_status(self) -> Dict:
        """获取所有爬虫的状态"""
        try:
            return self.crawler_manager.get_crawler_status()
        except Exception as e:
            self.logger.error(f"获取爬虫状态失败: {e}")
            return {}
    
    def download_images(self, 
                       crawler_type: str, 
                       query: str, 
                       pages: int = 1,
                       save_dir: Optional[str] = None) -> Dict:
        """
        下载图片的主要接口
        
        Args:
            crawler_type: 爬虫类型
            query: 搜索关键词
            pages: 页数
            save_dir: 保存目录
            
        Returns:
            下载结果
        """
        try:
            self.logger.info(f"开始下载图片: {crawler_type}, 关键词: {query}, 页数: {pages}")
            
            # 发送状态变化信号
            self.crawler_status_changed.emit(crawler_type, {"status": "downloading", "query": query})
            
            # 调用爬虫管理器下载图片
            result = self.crawler_manager.download_images(
                crawler_type=crawler_type,
                query=query,
                pages=pages,
                save_dir=save_dir
            )
            
            if "error" in result:
                # 下载失败
                self.download_error.emit(crawler_type, result["error"])
                self.crawler_status_changed.emit(crawler_type, {"status": "error", "error": result["error"]})
            else:
                # 下载成功
                self.download_completed.emit(crawler_type, result)
                self.crawler_status_changed.emit(crawler_type, {"status": "completed", "result": result})
            
            return result
            
        except Exception as e:
            error_msg = f"下载图片时出错: {e}"
            self.logger.error(error_msg)
            self.download_error.emit(crawler_type, error_msg)
            self.crawler_status_changed.emit(crawler_type, {"status": "error", "error": error_msg})
            return {"error": error_msg}
    
    def batch_download(self, 
                      crawler_type: str, 
                      queries: List[str], 
                      pages: int = 1,
                      save_dir: Optional[str] = None) -> Dict:
        """
        批量下载多个关键词的图片
        
        Args:
            crawler_type: 爬虫类型
            queries: 关键词列表
            pages: 每个关键词的页数
            save_dir: 保存目录
            
        Returns:
            批量下载结果
        """
        try:
            self.logger.info(f"开始批量下载: {crawler_type}, 关键词: {queries}, 页数: {pages}")
            
            # 发送状态变化信号
            self.crawler_status_changed.emit(crawler_type, {"status": "batch_downloading", "queries": queries})
            
            # 调用爬虫管理器批量下载
            result = self.crawler_manager.batch_download_multiple_queries(
                crawler_type=crawler_type,
                queries=queries,
                pages=pages,
                save_dir=save_dir
            )
            
            if "error" in result:
                # 批量下载失败
                self.download_error.emit(crawler_type, result["error"])
                self.crawler_status_changed.emit(crawler_type, {"status": "error", "error": result["error"]})
            else:
                # 批量下载成功
                self.download_completed.emit(crawler_type, result)
                self.crawler_status_changed.emit(crawler_type, {"status": "batch_completed", "result": result})
            
            return result
            
        except Exception as e:
            error_msg = f"批量下载时出错: {e}"
            self.logger.error(error_msg)
            self.download_error.emit(crawler_type, error_msg)
            self.crawler_status_changed.emit(crawler_type, {"status": "error", "error": error_msg})
            return {"error": error_msg}
    
    def get_download_history(self, save_dir: Optional[str] = None) -> Dict:
        """获取下载历史"""
        try:
            return self.crawler_manager.get_download_history(save_dir)
        except Exception as e:
            self.logger.error(f"获取下载历史失败: {e}")
            return {"error": str(e)}
    
    def cleanup_old_downloads(self, days: int = 30) -> Dict:
        """清理旧的下载文件"""
        try:
            return self.crawler_manager.cleanup_old_downloads(days=days)
        except Exception as e:
            self.logger.error(f"清理旧下载失败: {e}")
            return {"error": str(e)}
    
    def get_crawler_config(self, crawler_type: str) -> Dict:
        """获取爬虫配置"""
        try:
            return self.crawler_manager.get_crawler_config(crawler_type)
        except Exception as e:
            self.logger.error(f"获取爬虫配置失败: {e}")
            return {"error": str(e)}
    
    def update_crawler_config(self, crawler_type: str, **kwargs) -> Dict:
        """更新爬虫配置"""
        try:
            return self.crawler_manager.update_crawler_config(crawler_type, **kwargs)
        except Exception as e:
            self.logger.error(f"更新爬虫配置失败: {e}")
            return {"error": str(e)}
    
    def test_crawler_functionality(self) -> Dict:
        """
        测试爬虫功能
        在协调器启动时调用，验证爬虫系统是否正常工作
        """
        try:
            self.logger.info("开始测试爬虫功能...")
            
            # 获取爬虫状态
            status = self.get_crawler_status()
            self.logger.info(f"爬虫状态: {status}")
            
            # 测试配置获取
            config = self.get_crawler_config('unsplash')
            self.logger.info(f"Unsplash 配置: {config}")
            
            # 测试下载功能（使用较小的页数避免长时间等待）
            test_result = self.download_images(
                crawler_type='unsplash',
                query='test',
                pages=1
            )
            
            self.logger.info(f"爬虫功能测试完成: {test_result}")
            return {
                "status": "success",
                "crawler_status": status,
                "test_result": test_result
            }
            
        except Exception as e:
            error_msg = f"爬虫功能测试失败: {e}"
            self.logger.error(error_msg)
            return {"status": "error", "error": error_msg}
    
    def cleanup(self):
        """清理资源"""
        super().cleanup()
        self.logger.info("WebCrawlerHandler: 清理完成")

