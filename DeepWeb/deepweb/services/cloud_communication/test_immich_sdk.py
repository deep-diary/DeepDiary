"""
Immich Smart Search 功能测试脚本

根据 immich_smart_search.md 文档实现 search_smart 功能
参考: https://api.immich.app/endpoints/search/searchSmart

认证说明：
1. Immich SDK 支持两种认证方式：
   - API Key 认证（推荐）：直接使用 api_key，通过 x-api-key header 认证
   - Bearer Token 认证：使用 email + password 登录获取 access_token

2. Configuration 中的 username 和 password 参数：
   - 这些参数是用于 HTTP Basic Authentication 的（可选）
   - Immich API 不使用 HTTP Basic Auth，所以这些参数不是必须的
   - 如果需要 Bearer token，应该使用 AuthenticationApi.login() 方法
"""
from immich_python_sdk import (
    ApiClient, Configuration, SearchApi, SmartSearchDto,
    AuthenticationApi, LoginCredentialDto
)
from datetime import datetime
import json
import os
from pathlib import Path

# ========== 配置部分 ==========
# 从 config.json 读取配置
CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "config.json"
if CONFIG_PATH.exists():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        config_data = json.load(f)
        IMMICH_CONFIG = config_data.get("immich", {})
        print(f"已从配置文件加载 Immich 配置: {CONFIG_PATH}")
else:
    # 如果配置文件不存在，使用默认配置
    IMMICH_CONFIG = {
        "api_url": "http://127.0.0.1:2283/api",
        "api_key": "ZbQpVHwESQC4chEUJyVYoIyP6pVUFJvpRh1llIOYbw",
        "email": "deep-diary@qq.com",
        "password": "deep-diary666"
    }
    print("使用默认配置（配置文件不存在）")

# 方式1：使用 API Key 认证（推荐，最简单）
print("="*60)
print("方式1：使用 API Key 认证")
print("="*60)
configuration = Configuration(
    host=IMMICH_CONFIG["api_url"],
)
# 根据 configuration.py 的 auth_settings() 方法，api_key 的 key 应该是 'api_key'
# 这会在请求头中设置 'x-api-key'
configuration.api_key['api_key'] = IMMICH_CONFIG["api_key"]

# 创建客户端和 API 实例
client = ApiClient(configuration)
api_instance = SearchApi(client)

# 方式2：使用 Bearer Token 认证（可选，如果 API Key 不工作）
# 如果 API Key 认证失败，可以尝试使用 Bearer Token
USE_BEARER_TOKEN = False  # 设置为 True 以使用 Bearer token 认证

# 首先尝试 API Key 认证，如果失败则尝试 Bearer Token
try_api_key_first = True

if USE_BEARER_TOKEN:
    print("\n" + "="*60)
    print("方式2：使用 Bearer Token 认证")
    print("="*60)
    try:
        # 先创建一个基础配置（不需要认证）用于登录
        login_config = Configuration(host=IMMICH_CONFIG["api_url"])
        login_client = ApiClient(login_config)
        auth_api = AuthenticationApi(login_client)
        
        # 使用 email 和 password 登录
        login_dto = LoginCredentialDto(
            email=IMMICH_CONFIG["email"],
            password=IMMICH_CONFIG["password"]
        )
        print(f"正在使用 email '{IMMICH_CONFIG['email']}' 登录...")
        login_response = auth_api.login(login_credential_dto=login_dto)
        
        # 获取 access token
        access_token = login_response.access_token
        print(f"登录成功！已获取 Bearer token")
        
        # 使用 access token 创建新的配置
        configuration = Configuration(
            host=IMMICH_CONFIG["api_url"],
            access_token=access_token
        )
        client = ApiClient(configuration)
        api_instance = SearchApi(client)
        
    except Exception as e:
        print(f"Bearer token 认证失败: {e}")
        print("回退到 API Key 认证...")
        # 如果登录失败，继续使用 API Key

# ========== 测试认证 ==========
# 先测试认证是否成功（通过调用一个简单的 API）
print("\n" + "="*60)
print("测试认证...")
print("="*60)
try:
    # 尝试调用 search_smart 来测试认证
    test_dto = SmartSearchDto(query="test", size=1)
    test_result = api_instance.search_smart(smart_search_dto=test_dto)
    print("✓ 认证成功！API Key 认证正常工作")
except Exception as e:
    error_msg = str(e)
    if "401" in error_msg or "Unauthorized" in error_msg:
        print("✗ API Key 认证失败，尝试使用 Bearer Token 认证...")
        if IMMICH_CONFIG.get("email") and IMMICH_CONFIG.get("password"):
            try:
                # 尝试使用 Bearer Token
                login_config = Configuration(host=IMMICH_CONFIG["api_url"])
                login_client = ApiClient(login_config)
                auth_api = AuthenticationApi(login_client)
                
                login_dto = LoginCredentialDto(
                    email=IMMICH_CONFIG["email"],
                    password=IMMICH_CONFIG["password"]
                )
                print(f"正在使用 email '{IMMICH_CONFIG['email']}' 登录...")
                login_response = auth_api.login(login_credential_dto=login_dto)
                access_token = login_response.access_token
                print("✓ 登录成功！已获取 Bearer token")
                
                # 使用 access token 创建新的配置
                configuration = Configuration(
                    host=IMMICH_CONFIG["api_url"],
                    access_token=access_token
                )
                client = ApiClient(configuration)
                api_instance = SearchApi(client)
                
                # 再次测试
                test_result = api_instance.search_smart(smart_search_dto=test_dto)
                print("✓ Bearer Token 认证成功！")
            except Exception as login_error:
                print(f"✗ Bearer Token 认证也失败: {login_error}")
                raise
        else:
            print("✗ 认证失败，且未配置 email 和 password，无法尝试 Bearer Token 认证")
            raise
    else:
        print(f"✗ 其他错误: {e}")
        raise

# ========== 搜索功能 ==========
print("\n" + "="*60)
print("执行智能搜索")
print("="*60)
try:
    # 创建 SmartSearchDto 对象
    # query 是必需参数，其他参数都是可选的
    # 根据文档示例，可以设置以下参数：
    search_dto = SmartSearchDto(
        query="red clothes",  # 必需参数：搜索查询文本
        page=1,               # 页码
        withExif=True,        # 是否包含 EXIF 信息
        language="zh-CN",     # 语言设置
        size=5,               # 返回结果数量限制
        
        # 以下参数可根据需要添加：
        # city="Zhouxiang",   # 城市筛选
        # takenAfter=datetime(2025, 1, 1),  # 拍摄时间起始
        # takenBefore=datetime(2025, 12, 11, 23, 59, 59),  # 拍摄时间结束
        # personIds=[         # 人物 ID 列表
        #     "94777e17-bd75-4615-ac41-6f041b661af0",
        #     "8c9ce16f-433e-43a4-ab63-76769d39a00c"
        # ],
    )
    
    print("正在搜索...")
    print(f"搜索参数: query='{search_dto.query}', page={search_dto.page}, size={search_dto.size}")
    
    # 调用 search_smart 方法
    result = api_instance.search_smart(smart_search_dto=search_dto)
    
    # 打印结果
    print("\n" + "="*50)
    print("搜索结果:")
    print("="*50)
    print(f"资产总数: {result.assets.total}")
    print(f"返回数量: {result.assets.count}")
    
    if result.assets.items:
        print(f"\n资产列表:")
        for i, asset in enumerate(result.assets.items, 1):
            print(f"\n[{i}] ID: {asset.id}")
            # Pydantic 模型使用 snake_case 属性名
            print(f"    文件名: {asset.original_file_name}")
            print(f"    文件路径: {asset.original_path}")
            print(f"    创建时间: {asset.file_created_at}")
            print(f"    更新时间: {asset.updated_at}")
            print(f"    类型: {asset.type}")
            
            # 显示 EXIF 信息
            if asset.exif_info:
                exif = asset.exif_info
                exif_dict = exif.model_dump() if hasattr(exif, 'model_dump') else {}
                if exif_dict.get('city'):
                    print(f"    城市: {exif_dict['city']}")
                if exif_dict.get('make'):
                    model = exif_dict.get('model', '')
                    print(f"    相机: {exif_dict['make']} {model}".strip())
                if exif_dict.get('latitude') and exif_dict.get('longitude'):
                    print(f"    位置: {exif_dict['latitude']}, {exif_dict['longitude']}")
            
            # 显示人物信息
            if asset.people:
                people_names = [p.name if hasattr(p, 'name') else 'Unknown' for p in asset.people]
                if people_names:
                    print(f"    人物: {', '.join(people_names)}")
    else:
        print("\n未找到匹配的资产")
        
except Exception as e:
    print(f"\n错误: {e}")
    import traceback
    traceback.print_exc()