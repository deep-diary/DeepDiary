"""
测试 aioimmich 库的功能，特别是智能搜索功能
"""
import asyncio
import aiohttp
import json
from pathlib import Path

# 尝试导入 aioimmich
try:
    from aioimmich import Immich
    AIOIMMICH_AVAILABLE = True
except ImportError:
    AIOIMMICH_AVAILABLE = False
    print("aioimmich 未安装或不可用")

async def test_aioimmich():
    """测试 aioimmich 的基本功能和搜索功能"""
    if not AIOIMMICH_AVAILABLE:
        print("aioimmich 不可用，跳过测试")
        return
    
    # 从配置文件读取配置
    config_path = Path(__file__).parent.parent.parent / "config" / "config.json"
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
            immich_config = config_data.get("immich", {})
    else:
        immich_config = {
            "api_url": "http://127.0.0.1:2283/api",
            "api_key": "ZbQpVHwESQC4chEUJyVYoIyP6pVUFJvpRh1llIOYbw"
        }
    
    # aioimmich 需要 host 和 port 分开传递
    api_url_full = immich_config.get("api_url", "http://127.0.0.1:2283/api")
    # 解析 URL
    from urllib.parse import urlparse
    parsed = urlparse(api_url_full)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 2283
    use_ssl = parsed.scheme == "https"
    api_key = immich_config.get("api_key", "")
    
    print("="*60)
    print("aioimmich 功能测试")
    print("="*60)
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Use SSL: {use_ssl}")
    print(f"API Key: {api_key[:20]}...")
    
    async with aiohttp.ClientSession() as session:
        try:
            # 创建 Immich 客户端
            immich = Immich(session, api_key, host, port=port, use_ssl=use_ssl)
            
            print("\n1. 测试基本连接...")
            try:
                about = await immich.server.async_get_about_info()
                print(f"   ✓ 连接成功！服务器版本: {about.version if hasattr(about, 'version') else 'N/A'}")
            except Exception as e:
                print(f"   ✗ 连接失败: {e}")
                return
            
            print("\n2. 查看可用的 API 模块...")
            modules = [attr for attr in dir(immich) if not attr.startswith('_')]
            print(f"   可用模块: {', '.join(modules)}")
            
            print("\n3. 查看 Search 模块的方法...")
            if hasattr(immich, 'search'):
                search = immich.search
                search_methods = [m for m in dir(search) if not m.startswith('_') and callable(getattr(search, m))]
                print(f"   Search 方法: {', '.join(search_methods)}")
                
                # 检查是否有 smart_search
                has_smart_search = any('smart' in m.lower() for m in search_methods)
                print(f"   是否有 smart_search: {has_smart_search}")
                
                # 检查 search.api
                if hasattr(search, 'api'):
                    api_methods = [m for m in dir(search.api) if not m.startswith('_')]
                    print(f"   Search API 方法: {', '.join(api_methods)}")
            
            print("\n4. 尝试使用通用 API 调用方法进行智能搜索...")
            # 检查是否有通用的 API 调用方法
            if hasattr(immich.search, 'api') and hasattr(immich.search.api, 'async_do_request'):
                try:
                    # 尝试调用 smart search API
                    search_data = {
                        "query": "red clothes",
                        "page": 1,
                        "size": 5,
                        "withExif": True,
                        "language": "zh-CN"
                    }
                    
                    # 使用 async_do_request 调用
                    result = await immich.search.api.async_do_request(
                        method="POST",
                        path="/search/smart",
                        json=search_data
                    )
                    print(f"   ✓ 智能搜索成功！")
                    print(f"   结果类型: {type(result)}")
                    if hasattr(result, 'assets'):
                        print(f"   找到资产数: {len(result.assets.items) if hasattr(result.assets, 'items') else 'N/A'}")
                except Exception as e:
                    print(f"   ✗ 智能搜索失败: {e}")
                    import traceback
                    traceback.print_exc()
            
            print("\n5. 测试其他搜索方法...")
            try:
                # 测试 async_get_all
                if hasattr(immich.search, 'async_get_all'):
                    all_results = await immich.search.async_get_all()
                    print(f"   ✓ async_get_all 成功，返回类型: {type(all_results)}")
            except Exception as e:
                print(f"   ✗ async_get_all 失败: {e}")
            
        except Exception as e:
            print(f"\n错误: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_aioimmich())
