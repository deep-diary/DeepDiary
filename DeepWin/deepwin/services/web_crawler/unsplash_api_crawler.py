#!/usr/bin/env python3
"""
Unsplash API 爬虫类
使用官方API进行图片爬取，支持批量下载和分类存储
"""

import os
import time
import requests
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional
import logging

class UnsplashApiCrawler:
    """
    Unsplash API 爬虫类
    使用官方API进行图片爬取
    """
    
    def __init__(self, log_manager=None, config_manager=None):
        """
        初始化Unsplash API爬虫
        
        Args:
            log_manager: 日志管理器实例
            config_manager: 配置管理器实例
        """
        self.logger = log_manager.get_logger(__name__) if log_manager else self._setup_logging()
        self.config_manager = config_manager
        
        # 从环境变量或配置管理器获取API密钥
        self.access_key = self._get_access_key()
        
        # 配置参数
        self.max_workers = 5  # 线程池大小
        self.per_page = 10    # 每页数量
        self.delay = 1.0      # 请求延迟
        
        # 基础URL
        self.base_url = "https://api.unsplash.com"
        self.search_url = f"{self.base_url}/search/photos"

        # 保存目录
        self.save_dir = os.path.join(os.path.dirname(__file__), "../../../output/crawler_images")
        
        # 设置请求头
        self.headers = {"Authorization": f"Client-ID {self.access_key}"}
        
        self.logger.info("Unsplash API 爬虫初始化完成")
    
    def _setup_logging(self):
        """设置日志（如果没有传入日志管理器）"""
        # 使用统一的日志管理器，避免重复配置
        from deepwin.data_management.log_manager import LogManager
        log_manager = LogManager()
        return log_manager.get_logger(__name__)
    
    def _get_access_key(self) -> str:
        """获取API访问密钥"""
        # 优先从环境变量获取
        access_key = os.getenv("UNSPLASH_ACCESS_KEY")
        
        if access_key:
            self.logger.info("从环境变量获取到 Unsplash API 密钥")
            return access_key
        
        # 从配置管理器获取
        if self.config_manager:
            try:
                access_key = self.config_manager.get("crawlers.unsplash.access_key", "access_key")
                if access_key and access_key != "access_key":
                    self.logger.info("从配置管理器获取到 Unsplash API 密钥")
                    return access_key
            except Exception as e:
                self.logger.warning(f"从配置管理器获取API密钥失败: {e}")
        
        # 使用默认密钥（如果存在）
        default_key = "GTgPW-ey0ddMPulJeIx5mdvIE67mCOj6zPO5uJ_xtFc"
        self.logger.warning(f"使用默认API密钥，建议设置环境变量 UNSPLASH_ACCESS_KEY")
        return default_key
    
    def fetch_image_list(self, query: str, page: int = 1, per_page: Optional[int] = None) -> List[Dict]:
        """
        通过API获取图片列表
        
        Args:
            query: 搜索关键词
            page: 页码
            per_page: 每页数量
            
        Returns:
            图片列表
        """
        try:
            params = {
                "query": query, 
                "per_page": per_page or self.per_page, 
                "page": page
            }
            
            self.logger.info(f"搜索图片: {query}, 页码: {page}, 每页: {per_page or self.per_page}")
            
            response = requests.get(
                self.search_url, 
                headers=self.headers, 
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                total = data.get("total", 0)
                results = data.get("results", [])
                
                self.logger.info(f"搜索成功: 找到 {len(results)} 张图片，总计 {total} 张")
                return results
            else:
                self.logger.error(f"API请求失败: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            self.logger.error(f"获取图片列表失败: {e}")
            return []
    
    def download_image(self, img_data: Dict, save_dir: str, index: int) -> bool:
        """
        下载单张图片
        
        Args:
            img_data: 图片数据
            save_dir: 保存目录
            index: 图片索引
            
        Returns:
            是否下载成功
        """
        try:
            # 获取高清图片URL
            img_url = img_data["urls"]["full"]
            img_id = img_data.get("id", f"img_{index}")
            
            # 生成文件名
            filename = f"{img_id}.jpg"
            filepath = os.path.join(save_dir, filename)
            
            # 确保目录存在
            os.makedirs(save_dir, exist_ok=True)
            
            # 下载图片
            img_response = requests.get(img_url, timeout=30)
            if img_response.status_code == 200:
                with open(filepath, "wb") as f:
                    f.write(img_response.content)
                
                # 记录图片信息
                img_info = {
                    "id": img_id,
                    "filename": filename,
                    "url": img_url,
                    "description": img_data.get("description", ""),
                    "alt_description": img_data.get("alt_description", ""),
                    "width": img_data.get("width", 0),
                    "height": img_data.get("height", 0),
                    "download_time": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                
                self.logger.info(f"✅ 图片下载成功: {filename}")
                return True
            else:
                self.logger.error(f"❌ 图片下载失败: {img_url}, 状态码: {img_response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ 下载图片时出错: {e}")
            return False
    
    def batch_download(self, query: str, pages: int = 1, save_dir: Optional[str] = None) -> Dict:
        """
        批量下载图片
        
        Args:
            query: 搜索关键词
            pages: 爬取页数
            save_dir: 保存目录（如果为None，则使用默认目录）
            
        Returns:
            下载结果统计
        """
        if save_dir is None:
            save_dir = os.path.join(self.save_dir, query.lower())
        else:
            save_dir = os.path.join(save_dir, query.lower())
        
        self.logger.info(f"🚀 开始批量下载: {query}, 页数: {pages}, 保存目录: {save_dir}")
        
        start_time = time.time()
        total_images = 0
        downloaded_images = 0
        failed_downloads = 0
        
        try:
            # 获取所有图片
            all_images = []
            for page in range(1, pages + 1):
                images = self.fetch_image_list(query, page)
                if images:
                    all_images.extend(images)
                    total_images += len(images)
                    
                    # 添加延迟避免API限制
                    if page < pages:
                        time.sleep(self.delay)
                else:
                    self.logger.warning(f"第 {page} 页未获取到图片")
            
            if not all_images:
                self.logger.warning("未获取到任何图片")
                return {
                    "query": query,
                    "total_images": 0,
                    "downloaded_images": 0,
                    "failed_downloads": 0,
                    "success_rate": "0%",
                    "total_time": 0
                }
            
            # 使用线程池下载
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = []
                for i, img_data in enumerate(all_images):
                    self.logger.info(f"loop {i} 下载图片: {img_data['id']}")
                    future = executor.submit(self.download_image, img_data, save_dir, i)
                    futures.append(future)
                
                # 等待所有下载完成
                for future in futures:
                    if future.result():
                        downloaded_images += 1
                    else:
                        failed_downloads += 1
                    
                    # 添加延迟避免过快请求
                    time.sleep(self.delay)
            
            total_time = time.time() - start_time
            success_rate = f"{(downloaded_images/total_images*100):.1f}%" if total_images > 0 else "0%"
            
            result = {
                "query": query,
                "total_images": total_images,
                "downloaded_images": downloaded_images,
                "failed_downloads": failed_downloads,
                "success_rate": success_rate,
                "total_time": total_time,
                "save_dir": save_dir
            }
            
            self.logger.info(f"🎉 批量下载完成: {downloaded_images}/{total_images} 成功, 成功率: {success_rate}")
            self.logger.info(f"⏱️ 总耗时: {total_time:.2f} 秒")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ 批量下载过程中出现错误: {e}")
            return {
                "query": query,
                "error": str(e),
                "total_images": total_images,
                "downloaded_images": downloaded_images,
                "failed_downloads": failed_downloads,
                "success_rate": "0%",
                "total_time": time.time() - start_time
            }
    
    def get_image_info(self, img_data: Dict) -> Dict:
        """
        获取图片详细信息
        
        Args:
            img_data: 图片数据
            
        Returns:
            图片信息字典
        """
        return {
            "id": img_data.get("id", ""),
            "description": img_data.get("description", ""),
            "alt_description": img_data.get("alt_description", ""),
            "width": img_data.get("width", 0),
            "height": img_data.get("height", 0),
            "urls": img_data.get("urls", {}),
            "user": img_data.get("user", {}),
            "created_at": img_data.get("created_at", ""),
            "likes": img_data.get("likes", 0)
        }

def main():
    """主函数 - 测试爬虫"""
    try:
        print("🚀 开始测试 Unsplash API 爬虫...")
        
        # 创建爬虫实例
        crawler = UnsplashApiCrawler()
        
        # 测试参数
        query = "cat"
        pages = 1
        
        print(f"🔍 搜索关键词: {query}")
        print(f"📄 爬取页数: {pages}")
        
        # 执行批量下载
        result = crawler.batch_download(query, pages)
        
        print("\n📊 下载结果:")
        for key, value in result.items():
            print(f"  {key}: {value}")
        
        print("\n🎉 测试完成！")
        
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断测试")
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {str(e)}")

if __name__ == "__main__":
    main()
