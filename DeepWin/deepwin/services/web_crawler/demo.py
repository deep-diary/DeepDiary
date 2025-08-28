#!/usr/bin/env python3
"""
DeepWin 爬虫服务演示文件
展示爬虫包的主要功能和使用方法

使用方法:
    python demo.py                    # 运行完整演示
    python demo.py --component=baidu # 只运行特定组件演示
"""

import os
import sys
import time
import argparse
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from deepwin.config.config_manager import ConfigManager
    from deepwin.data_management.log_manager import LogManager
    from deepwin.services.web_crawler import UnsplashApiCrawler, BaiduCrawler, CrawlerManager
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print("请确保在正确的环境中运行，并且所有依赖已安装")
    sys.exit(1)

def setup_environment():
    """设置演示环境"""
    print("🔧 设置演示环境...")
    
    # 创建日志和配置管理器
    log_manager = LogManager()
    config_manager = ConfigManager(log_manager=log_manager)
    
    # 检查输出目录
    output_dir = Path(project_root) / "output" / "crawler_images"
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 输出目录: {output_dir}")
    
    return log_manager, config_manager, output_dir

def demo_unsplash_crawler(log_manager, config_manager):
    """演示 Unsplash API 爬虫"""
    print("\n" + "=" * 60)
    print("🖼️ 演示 Unsplash API 爬虫")
    print("=" * 60)
    
    try:
        # 创建爬虫实例
        crawler = UnsplashApiCrawler(log_manager=log_manager, config_manager=config_manager)
        
        # 测试搜索
        print("🔍 搜索图片...")
        images = crawler.fetch_image_list("nature", 1, 5)
        print(f"找到 {len(images)} 张图片")
        
        if images:
            # 显示第一张图片信息
            first_image = images[0]
            info = crawler.get_image_info(first_image)
            print(f"第一张图片信息: {info}")
        
        # 测试下载（小批量）
        print("\n📥 测试下载...")
        result = crawler.batch_download("nature", 1)
        print(f"下载结果: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Unsplash 爬虫演示失败: {e}")
        return False

def demo_baidu_crawler(log_manager, config_manager):
    """演示百度爬虫"""
    print("\n" + "=" * 60)
    print("🔍 演示百度爬虫")
    print("=" * 60)
    
    try:
        # 创建爬虫实例
        crawler = BaiduCrawler(log_manager=log_manager, config_manager=config_manager)
        
        # 测试批量下载
        print("📥 测试批量下载...")
        test_queries = ["风景", "动物"]  # 使用更合适的测试关键词
        results = crawler.batch_download(test_queries, total_pages=1)
        
        print("批量下载结果:")
        for query, result in results.items():
            if query != "summary":
                status = "✅" if result.get("status") == "success" else "❌"
                print(f"{status} {query}: {result}")
        
        if "summary" in results:
            summary = results["summary"]
            print(f"\n📊 总结: 处理 {summary['total_queries']} 个关键词, "
                  f"成功 {summary['success_count']} 个, "
                  f"耗时 {summary['total_time']:.2f} 秒")
        
        return True
        
    except Exception as e:
        print(f"❌ 百度爬虫演示失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def demo_crawler_manager(log_manager, config_manager):
    """演示爬虫管理器"""
    print("\n" + "=" * 60)
    print("🎛️ 演示爬虫管理器")
    print("=" * 60)
    
    try:
        # 创建爬虫管理器
        manager = CrawlerManager(log_manager=log_manager, config_manager=config_manager)
        
        # 显示爬虫状态
        print("📊 爬虫状态:")
        status = manager.get_crawler_status()
        for crawler_type, info in status.items():
            status_icon = "✅" if info["status"] == "active" else "❌"
            print(f"{status_icon} {crawler_type}: {info}")
        
        # 显示可用爬虫
        print(f"\n🔧 可用爬虫: {manager.list_crawlers()}")
        
        # 获取爬虫配置
        print("\n⚙️ 爬虫配置:")
        for crawler_type in manager.list_crawlers():
            config = manager.get_crawler_config(crawler_type)
            print(f"{crawler_type}: {config}")
        
        # 测试下载历史
        print("\n📚 下载历史:")
        history = manager.get_download_history()
        if "error" not in history:
            print(f"总关键词数: {history['total_keywords']}")
            print(f"总图片数: {history['total_images']}")
            for keyword, info in history.get('keywords', {}).items():
                print(f"  {keyword}: {info['image_count']} 张图片")
        else:
            print("暂无下载历史")
        
        return True
        
    except Exception as e:
        print(f"❌ 爬虫管理器演示失败: {e}")
        return False

def demo_integration(log_manager, config_manager):
    """演示集成使用"""
    print("\n" + "=" * 60)
    print("🔗 演示集成使用")
    print("=" * 60)
    
    try:
        # 创建爬虫管理器
        manager = CrawlerManager(log_manager=log_manager, config_manager=config_manager)
        
        # 使用多个爬虫下载不同关键词
        print("🔄 使用多个爬虫下载图片...")
        
        # 使用更合适的测试关键词
        queries = ["landscape", "wildlife", "architecture"]
        result = manager.download_with_multiple_crawlers(queries, 1)
        
        print("多爬虫下载结果:")
        for crawler_type, crawler_result in result.get('results', {}).items():
            if "error" not in crawler_result:
                print(f"✅ {crawler_type}: 成功")
            else:
                print(f"❌ {crawler_type}: {crawler_result['error']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 集成演示失败: {e}")
        return False

def demo_batch_operations(log_manager, config_manager):
    """演示批量操作"""
    print("\n" + "=" * 60)
    print("📦 演示批量操作")
    print("=" * 60)
    
    try:
        manager = CrawlerManager(log_manager=log_manager, config_manager=config_manager)
        
        # 批量下载多个关键词
        print("🔄 批量下载多个关键词...")
        queries = ["sunset", "mountain", "ocean"]
        result = manager.batch_download_multiple_queries('unsplash', queries, 1)
        
        print("批量下载结果:")
        for query, query_result in result.items():
            if query != "summary":
                status = "✅" if query_result.get("status") == "success" else "❌"
                print(f"{status} {query}: {query_result}")
        
        if "summary" in result:
            summary = result["summary"]
            print(f"\n📊 总结: 处理 {summary['total_queries']} 个关键词, "
                  f"成功 {summary['success_count']} 个, "
                  f"耗时 {summary['total_time']:.2f} 秒")
        
        return True
        
    except Exception as e:
        print(f"❌ 批量操作演示失败: {e}")
        return False

def main():
    """主演示函数"""
    parser = argparse.ArgumentParser(description="DeepWin 爬虫服务演示")
    parser.add_argument('--component', choices=['unsplash', 'baidu', 'manager', 'integration', 'batch'], 
                       help='指定要演示的组件')
    args = parser.parse_args()
    
    print("🚀 DeepWin 爬虫服务演示")
    print("=" * 60)
    
    # 设置环境
    log_manager, config_manager, output_dir = setup_environment()
    
    # 记录演示结果
    demo_results = {}
    
    try:
        if args.component:
            # 运行指定组件演示
            if args.component == 'unsplash':
                demo_results['unsplash'] = demo_unsplash_crawler(log_manager, config_manager)
            elif args.component == 'baidu':
                demo_results['baidu'] = demo_baidu_crawler(log_manager, config_manager)
            elif args.component == 'manager':
                demo_results['manager'] = demo_crawler_manager(log_manager, config_manager)
            elif args.component == 'integration':
                demo_results['integration'] = demo_integration(log_manager, config_manager)
            elif args.component == 'batch':
                demo_results['batch'] = demo_batch_operations(log_manager, config_manager)
        else:
            # 运行完整演示
            print("🔄 运行完整演示...")
            demo_results['unsplash'] = demo_unsplash_crawler(log_manager, config_manager)
            time.sleep(1)
            
            demo_results['baidu'] = demo_baidu_crawler(log_manager, config_manager)
            time.sleep(1)
            
            demo_results['manager'] = demo_crawler_manager(log_manager, config_manager)
            time.sleep(1)
            
            demo_results['integration'] = demo_integration(log_manager, config_manager)
            time.sleep(1)
            
            demo_results['batch'] = demo_batch_operations(log_manager, config_manager)
        
        # 显示演示结果
        print("\n" + "=" * 60)
        print("📊 演示结果总结")
        print("=" * 60)
        
        success_count = sum(1 for result in demo_results.values() if result)
        total_count = len(demo_results)
        
        for component, result in demo_results.items():
            status = "✅ 成功" if result else "❌ 失败"
            print(f"{component.capitalize()}: {status}")
        
        print(f"\n总体结果: {success_count}/{total_count} 个组件演示成功")
        
        if success_count == total_count:
            print("🎉 所有演示完成！")
        else:
            print("⚠️ 部分演示失败，请检查错误信息")
        
        # 显示输出目录结构
        print("\n📁 输出目录结构:")
        if output_dir.exists():
            for item in output_dir.iterdir():
                if item.is_dir():
                    image_count = len([f for f in item.iterdir() 
                                     if f.suffix.lower() in ('.jpg', '.jpeg', '.png', '.gif')])
                    print(f"  📂 {item.name}/ ({image_count} 张图片)")
        
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断演示")
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
