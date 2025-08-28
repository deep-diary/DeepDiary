#!/usr/bin/env python3
"""
爬虫管理器
作为对接协调器的窗口，管理所有爬虫实例
"""

import os
import time
from typing import Dict, List, Optional, Union
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

from .unsplash_api_crawler import UnsplashApiCrawler
from .baidu_crawler import BaiduCrawler


class CrawlerManager:
    """
    爬虫管理器类
    统一管理所有爬虫实例，提供统一的接口
    """
    
    def __init__(self, log_manager=None, config_manager=None):
        """
        初始化爬虫管理器
        
        Args:
            log_manager: 日志管理器实例
            config_manager: 配置管理器实例
        """
        self.logger = log_manager.get_logger(__name__) if log_manager else self._setup_logging()
        self.config_manager = config_manager
        
        # 爬虫实例字典
        self.crawlers = {}
        
        # 输出目录配置
        if self.config_manager:
            self.output_base_dir = self.config_manager.get("web_crawler.output_dir", "output/crawler_images")
        else:
            self.output_base_dir = "output/crawler_images"
        
        # 初始化爬虫实例
        self._init_crawlers()
        
        self.logger.info("爬虫管理器初始化完成")
    
    def _setup_logging(self):
        """设置日志（如果没有传入日志管理器）"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def _init_crawlers(self):
        """初始化所有爬虫实例"""
        try:
            # 从配置管理器获取爬虫配置
            if self.config_manager:
                unsplash_config = self.config_manager.get("web_crawler.unsplash", {})
                baidu_config = self.config_manager.get("web_crawler.baidu", {})
                global_config = self.config_manager.get("web_crawler.global", {})
                
                # 检查爬虫是否启用
                if unsplash_config.get("enabled", True):
                    self.crawlers['unsplash'] = UnsplashApiCrawler(
                        log_manager=None,
                        config_manager=self.config_manager
                    )
                    self.logger.info("✅ Unsplash API 爬虫初始化成功")
                else:
                    self.logger.info("⚠️ Unsplash 爬虫已禁用")
                
                if baidu_config.get("enabled", True):
                    self.crawlers['baidu'] = BaiduCrawler(
                        log_manager=None,
                        config_manager=self.config_manager,
                        t=baidu_config.get("time_sleep", 0.1)
                    )
                    self.logger.info("✅ 百度爬虫初始化成功")
                else:
                    self.logger.info("⚠️ 百度爬虫已禁用")
            else:
                # 如果没有配置管理器，使用默认配置
                self.crawlers['unsplash'] = UnsplashApiCrawler(
                    log_manager=None,
                    config_manager=None
                )
                self.crawlers['baidu'] = BaiduCrawler(
                    log_manager=None,
                    config_manager=None,
                    t=0.1
                )
                self.logger.info("✅ 使用默认配置初始化爬虫")
            
        except Exception as e:
            self.logger.error(f"初始化爬虫时出错: {e}")
    
    def get_crawler(self, crawler_type: str) -> Optional[Union[UnsplashApiCrawler, BaiduCrawler]]:
        """
        获取指定类型的爬虫实例
        
        Args:
            crawler_type: 爬虫类型 ('unsplash' 或 'baidu')
            
        Returns:
            爬虫实例或None
        """
        return self.crawlers.get(crawler_type)
    
    def list_crawlers(self) -> List[str]:
        """获取所有可用的爬虫类型"""
        return list(self.crawlers.keys())
    
    def get_crawler_status(self) -> Dict:
        """获取所有爬虫的状态信息"""
        status = {}
        for crawler_type, crawler in self.crawlers.items():
            status[crawler_type] = {
                "type": type(crawler).__name__,
                "status": "active" if crawler else "inactive",
                "initialized": crawler is not None
            }
        return status
    
    def download_images(self, 
                       crawler_type: str, 
                       query: str, 
                       pages: int = 1, 
                       save_dir: Optional[str] = None,
                       **kwargs) -> Dict:
        """
        使用指定爬虫下载图片
        
        Args:
            crawler_type: 爬虫类型
            query: 搜索关键词
            pages: 页数
            save_dir: 保存目录
            **kwargs: 其他参数
            
        Returns:
            下载结果
        """
        crawler = self.get_crawler(crawler_type)
        if not crawler:
            return {"error": f"爬虫类型 {crawler_type} 不存在"}
        
        try:
            self.logger.info(f"开始使用 {crawler_type} 爬虫下载图片: {query}")
            
            if crawler_type == 'unsplash':
                result = crawler.batch_download(query, pages, save_dir)
            elif crawler_type == 'baidu':
                # 百度爬虫的start方法参数：word, total_page=1, start_page=1, per_page=10
                # 注意：百度爬虫不支持save_dir参数，它使用默认的输出目录
                result = crawler.start(query, pages, 1, 10)
                result = {
                    "query": query,
                    "pages": pages,
                    "status": "completed",
                    "crawler": crawler_type
                }
            else:
                return {"error": f"不支持的爬虫类型: {crawler_type}"}
            
            result["crawler_type"] = crawler_type
            return result
            
        except Exception as e:
            self.logger.error(f"使用 {crawler_type} 爬虫下载图片时出错: {e}")
            return {
                "error": str(e),
                "crawler_type": crawler_type,
                "query": query
            }
    
    def batch_download_multiple_queries(self, 
                                      crawler_type: str, 
                                      queries: List[str], 
                                      pages: int = 1,
                                      save_dir: Optional[str] = None,
                                      max_workers: int = 3) -> Dict:
        """
        批量下载多个关键词的图片
        
        Args:
            crawler_type: 爬虫类型
            queries: 关键词列表
            pages: 每个关键词的页数
            save_dir: 基础保存目录
            max_workers: 最大并发数
            
        Returns:
            批量下载结果
        """
        crawler = self.get_crawler(crawler_type)
        if not crawler:
            return {"error": f"爬虫类型 {crawler_type} 不存在"}
        
        try:
            self.logger.info(f"开始批量下载: {len(queries)} 个关键词, 爬虫: {crawler_type}")
            
            if crawler_type == 'unsplash':
                # Unsplash爬虫支持批量下载
                results = {}
                for query in queries:
                    query_save_dir = os.path.join(save_dir, query.lower()) if save_dir else None
                    result = crawler.batch_download(query, pages, query_save_dir)
                    results[query] = result
                    time.sleep(1)  # 避免API限制
                
                return {
                    "crawler_type": crawler_type,
                    "total_queries": len(queries),
                    "results": results
                }
                
            elif crawler_type == 'baidu':
                # 百度爬虫支持批量下载
                result = crawler.batch_download(queries, pages, save_dir)
                result["crawler_type"] = crawler_type
                return result
                
            else:
                return {"error": f"不支持的爬虫类型: {crawler_type}"}
                
        except Exception as e:
            self.logger.error(f"批量下载时出错: {e}")
            return {
                "error": str(e),
                "crawler_type": crawler_type,
                "queries": queries
            }
    
    def download_with_multiple_crawlers(self, 
                                      queries: List[str], 
                                      pages: int = 1,
                                      save_dir: Optional[str] = None) -> Dict:
        """
        使用多个爬虫同时下载图片
        
        Args:
            queries: 关键词列表
            pages: 每个关键词的页数
            save_dir: 基础保存目录
            
        Returns:
            多爬虫下载结果
        """
        results = {}
        
        for crawler_type in self.crawlers.keys():
            try:
                self.logger.info(f"使用 {crawler_type} 爬虫下载图片")
                
                if crawler_type == 'unsplash':
                    # Unsplash适合高质量图片
                    result = self.batch_download_multiple_queries(
                        crawler_type, queries[:len(queries)//2], pages, save_dir
                    )
                else:
                    # 百度爬虫处理剩余关键词
                    result = self.batch_download_multiple_queries(
                        crawler_type, queries[len(queries)//2:], pages, save_dir
                    )
                
                results[crawler_type] = result
                
            except Exception as e:
                self.logger.error(f"使用 {crawler_type} 爬虫时出错: {e}")
                results[crawler_type] = {"error": str(e)}
        
        return {
            "total_crawlers": len(results),
            "results": results
        }
    
    def get_download_history(self, save_dir: Optional[str] = None) -> Dict:
        """
        获取下载历史信息
        
        Args:
            save_dir: 保存目录
            
        Returns:
            下载历史统计
        """
        if save_dir is None:
            save_dir = self.output_base_dir
        
        history = {}
        
        try:
            if os.path.exists(save_dir):
                for item in os.listdir(save_dir):
                    item_path = os.path.join(save_dir, item)
                    if os.path.isdir(item_path):
                        # 统计每个关键词目录下的图片数量
                        image_count = len([f for f in os.listdir(item_path) 
                                         if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))])
                        history[item] = {
                            "image_count": image_count,
                            "path": item_path
                        }
            
            return {
                "total_keywords": len(history),
                "total_images": sum(h["image_count"] for h in history.values()),
                "keywords": history
            }
            
        except Exception as e:
            self.logger.error(f"获取下载历史时出错: {e}")
            return {"error": str(e)}
    
    def cleanup_old_downloads(self, save_dir: Optional[str] = None, days: int = 30) -> Dict:
        """
        清理旧的下载文件
        
        Args:
            save_dir: 保存目录
            days: 保留天数
            
        Returns:
            清理结果
        """
        if save_dir is None:
            save_dir = self.output_base_dir
        
        try:
            import shutil
            from datetime import datetime, timedelta
            
            cutoff_time = datetime.now() - timedelta(days=days)
            cleaned_files = 0
            cleaned_dirs = 0
            
            if os.path.exists(save_dir):
                for item in os.listdir(save_dir):
                    item_path = os.path.join(save_dir, item)
                    if os.path.isdir(item_path):
                        # 检查目录修改时间
                        mtime = datetime.fromtimestamp(os.path.getmtime(item_path))
                        if mtime < cutoff_time:
                            shutil.rmtree(item_path)
                            cleaned_dirs += 1
                            self.logger.info(f"清理旧目录: {item}")
            
            return {
                "cleaned_dirs": cleaned_dirs,
                "cleaned_files": cleaned_files,
                "cutoff_days": days
            }
            
        except Exception as e:
            self.logger.error(f"清理旧文件时出错: {e}")
            return {"error": str(e)}
    
    def get_global_config(self) -> Dict:
        """
        获取爬虫全局配置信息
        
        Returns:
            全局配置信息
        """
        if not self.config_manager:
            return {"error": "配置管理器未初始化"}
        
        try:
            return self.config_manager.get("web_crawler.global", {})
        except Exception as e:
            return {"error": str(e)}
    
    def get_crawler_config(self, crawler_type: str) -> Dict:
        """
        获取爬虫配置信息（从配置管理器读取）
        
        Args:
            crawler_type: 爬虫类型
            
        Returns:
            配置信息
        """
        if not self.config_manager:
            return {"error": "配置管理器未初始化"}
        
        try:
            config = self.config_manager.get(f"web_crawler.{crawler_type}", {})
            config["crawler_type"] = crawler_type
            return config
            
        except Exception as e:
            return {"error": str(e), "crawler_type": crawler_type}
    
    def update_crawler_config(self, crawler_type: str, **kwargs) -> Dict:
        """
        更新爬虫配置（通过配置管理器）
        
        Args:
            crawler_type: 爬虫类型
            **kwargs: 配置参数
            
        Returns:
            更新结果
        """
        if not self.config_manager:
            return {"error": "配置管理器未初始化"}
        
        try:
            # 通过配置管理器更新配置
            current_config = self.config_manager.get(f"web_crawler.{crawler_type}", {})
            updated_config = {**current_config, **kwargs}
            
            # 这里可以添加配置验证逻辑
            if crawler_type == 'unsplash':
                if 'access_key' in kwargs and not kwargs['access_key']:
                    return {"error": "Unsplash access_key 不能为空"}
            
            # 更新配置管理器中的配置
            self.config_manager.set(f"web_crawler.{crawler_type}", updated_config)
            
            self.logger.info(f"通过配置管理器更新 {crawler_type} 爬虫配置: {kwargs}")
            return {"status": "success", "updated_config": kwargs}
            
        except Exception as e:
            self.logger.error(f"更新爬虫配置时出错: {e}")
            return {"error": str(e)}
    def cleanup(self):
        """
        清理爬虫管理器
        """
        self.crawlers = {}
        self.logger.info("爬虫管理器已清理")


def main():
    """主函数 - 测试爬虫管理器"""
    try:
        print("🚀 开始测试爬虫管理器...")
        
        # 创建爬虫管理器
        manager = CrawlerManager()
        
        # 显示爬虫状态
        print("\n📊 爬虫状态:")
        status = manager.get_crawler_status()
        for crawler_type, info in status.items():
            status_icon = "✅" if info["status"] == "active" else "❌"
            print(f"{status_icon} {crawler_type}: {info}")
        
        # 显示可用爬虫
        print(f"\n🔧 可用爬虫: {manager.list_crawlers()}")
        
        # 测试下载
        test_query = "cat"
        print(f"\n🔄 测试下载: {test_query}")
        
        result = manager.download_images('unsplash', test_query, 1)
        print(f"下载结果: {result}")
        
        print("\n🎉 测试完成！")
        
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断测试")
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {str(e)}")


if __name__ == "__main__":
    main()
