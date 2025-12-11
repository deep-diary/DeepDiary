# Immich Python SDK 核心文件详细分析

本文档详细分析 `immich_python_sdk` 的 5 个核心文件的作用、使用方法和实际应用场景。

## 文件概览

| 文件 | 作用 | 使用频率 |
|------|------|----------|
| `configuration.py` | 配置管理（认证、URL、SSL等） | ⭐⭐⭐⭐⭐ |
| `api_client.py` | API 客户端核心（请求/响应处理） | ⭐⭐⭐⭐⭐ |
| `api_response.py` | API 响应对象封装 | ⭐⭐⭐⭐ |
| `rest.py` | 底层 HTTP 客户端（基于 urllib3） | ⭐⭐⭐ |
| `exceptions.py` | 异常处理 | ⭐⭐⭐⭐ |

---

## 1. configuration.py - 配置管理

### 作用
管理 Immich API 客户端的所有配置，包括：
- 服务器地址和端口
- 认证信息（API Key、Bearer Token、用户名密码）
- SSL/TLS 设置
- 代理设置
- 超时设置
- 调试选项

### 核心功能

#### 1.1 初始化配置

```python
from immich_python_sdk import Configuration

# 方式1：基本配置
configuration = Configuration(
    host="http://127.0.0.1:2283/api"
)
configuration.api_key['api_key'] = 'your-api-key'

# 方式2：完整配置
configuration = Configuration(
    host="http://127.0.0.1:2283/api",
    api_key={'api_key': 'your-api-key'},
    access_token='bearer-token',  # 可选，用于 Bearer 认证
    username='user',  # 可选，用于 HTTP Basic Auth（Immich 不使用）
    password='pass',  # 可选，用于 HTTP Basic Auth（Immich 不使用）
    verify_ssl=True,  # SSL 验证
    ssl_ca_cert='/path/to/ca.crt',  # CA 证书
    proxy='http://proxy:8080',  # 代理设置
    retries=3,  # 重试次数
    debug=False  # 调试模式
)
```

#### 1.2 认证方式

```python
# 方式1：API Key 认证（推荐）
configuration.api_key['api_key'] = 'your-api-key'
# 这会在请求头中设置: x-api-key: your-api-key

# 方式2：Bearer Token 认证
configuration.access_token = 'your-bearer-token'
# 这会在请求头中设置: Authorization: Bearer your-bearer-token

# 方式3：Cookie 认证（较少使用）
configuration.api_key['cookie'] = 'your-cookie-value'
```

#### 1.3 获取认证设置

```python
# 获取认证头信息
auth_settings = configuration.auth_settings()
# 返回: {
#   'api_key': {'type': 'api_key', 'in': 'header', 'key': 'x-api-key', 'value': '...'},
#   'bearer': {'type': 'bearer', 'in': 'header', 'key': 'Authorization', 'value': 'Bearer ...'}
# }
```

#### 1.4 默认配置管理

```python
# 设置默认配置
Configuration.set_default(configuration)

# 获取默认配置
default_config = Configuration.get_default()

# 获取默认配置的副本
config_copy = Configuration.get_default_copy()
```

### 实际应用场景

```python
# 场景1：从配置文件读取配置
import json
from immich_python_sdk import Configuration

with open('config.json') as f:
    config_data = json.load(f)
    
configuration = Configuration(
    host=config_data['immich']['api_url']
)
configuration.api_key['api_key'] = config_data['immich']['api_key']

# 场景2：多环境配置
def get_config(env='dev'):
    configs = {
        'dev': Configuration(host='http://localhost:2283/api'),
        'prod': Configuration(host='https://immich.example.com/api')
    }
    config = configs[env]
    config.api_key['api_key'] = os.getenv('IMMICH_API_KEY')
    return config

# 场景3：动态切换认证方式
configuration = Configuration(host='...')
if use_bearer_token:
    configuration.access_token = get_token_from_login()
else:
    configuration.api_key['api_key'] = api_key
```

---

## 2. api_client.py - API 客户端核心

### 作用
这是 SDK 的核心类，负责：
- 序列化请求数据
- 发送 HTTP 请求
- 反序列化响应数据
- 处理认证
- 错误处理

### 核心功能

#### 2.1 初始化客户端

```python
from immich_python_sdk import ApiClient, Configuration

# 方式1：使用配置对象
configuration = Configuration(host='...')
client = ApiClient(configuration)

# 方式2：使用默认配置
client = ApiClient()  # 使用 Configuration.get_default()

# 方式3：作为上下文管理器
with ApiClient(configuration) as client:
    # 使用 client
    pass
```

#### 2.2 核心方法

##### 2.2.1 `call_api()` - 发送 HTTP 请求

```python
# 这是底层方法，通常不直接调用
# 但可以用于自定义请求
response = client.call_api(
    method='POST',
    url='http://127.0.0.1:2283/api/search/smart',
    header_params={'x-api-key': '...'},
    body={'query': 'red clothes'},
    _request_timeout=30
)
# 返回: rest.RESTResponse 对象
```

##### 2.2.2 `response_deserialize()` - 反序列化响应

```python
# 将 RESTResponse 转换为 ApiResponse 对象
response_data = client.call_api(...)
response_data.read()  # 必须先读取数据

api_response = client.response_deserialize(
    response_data=response_data,
    response_types_map={
        '200': 'SearchResponseDto',  # 状态码 -> 响应类型
        '400': 'ErrorDto'
    }
)
# 返回: ApiResponse[SearchResponseDto] 对象
# api_response.data 包含反序列化后的数据
# api_response.status_code 包含 HTTP 状态码
# api_response.headers 包含响应头
# api_response.raw_data 包含原始响应数据
```

##### 2.2.3 `param_serialize()` - 序列化请求参数

```python
# 将请求参数序列化为 HTTP 请求格式
method, url, headers, body, post_params = client.param_serialize(
    method='POST',
    resource_path='/search/smart',
    path_params={},  # URL 路径参数
    query_params={'page': 1},  # 查询参数
    header_params={},  # 请求头
    body={'query': 'red clothes'},  # 请求体
    post_params=[],  # POST 表单参数
    files={},  # 文件上传
    auth_settings=configuration.auth_settings()  # 认证设置
)
```

##### 2.2.4 `sanitize_for_serialization()` - 数据序列化

```python
# 将 Python 对象转换为可序列化的格式
data = {
    'query': 'red clothes',
    'date': datetime.now(),
    'tags': ['tag1', 'tag2']
}
serialized = client.sanitize_for_serialization(data)
# datetime 会被转换为 ISO 格式字符串
# 其他对象也会被适当转换
```

##### 2.2.5 `deserialize()` - 数据反序列化

```python
# 将 JSON 字符串反序列化为 Python 对象
json_text = '{"id": "123", "name": "test"}'
obj = client.deserialize(
    response_text=json_text,
    response_type='AssetResponseDto',  # 目标类型
    content_type='application/json'
)
# 返回: AssetResponseDto 对象
```

### 实际应用场景

```python
# 场景1：自定义 API 调用（绕过高级 API）
from immich_python_sdk import ApiClient, Configuration

config = Configuration(host='http://127.0.0.1:2283/api')
config.api_key['api_key'] = 'your-key'
client = ApiClient(config)

# 手动构建请求
method, url, headers, body, _ = client.param_serialize(
    method='POST',
    resource_path='/search/smart',
    body={'query': 'red clothes', 'size': 10},
    auth_settings=config.auth_settings()
)

# 发送请求
response = client.call_api(method, url, headers, body)
response.read()

# 反序列化响应
api_response = client.response_deserialize(
    response,
    response_types_map={'200': 'SearchResponseDto'}
)

print(api_response.data.assets.total)

# 场景2：批量处理请求
def batch_search(client, queries):
    results = []
    for query in queries:
        # 使用 param_serialize 准备请求
        method, url, headers, body, _ = client.param_serialize(
            method='POST',
            resource_path='/search/smart',
            body={'query': query},
            auth_settings=client.configuration.auth_settings()
        )
        # 发送请求
        response = client.call_api(method, url, headers, body)
        response.read()
        # 反序列化
        api_response = client.response_deserialize(
            response,
            response_types_map={'200': 'SearchResponseDto'}
        )
        results.append(api_response.data)
    return results
```

---

## 3. api_response.py - API 响应对象

### 作用
封装 API 响应，提供结构化的响应数据访问。

### 核心功能

#### 3.1 ApiResponse 类

```python
from immich_python_sdk.api_response import ApiResponse
from typing import Generic, TypeVar

T = TypeVar('T')

class ApiResponse(BaseModel, Generic[T]):
    status_code: int      # HTTP 状态码
    headers: dict         # HTTP 响应头
    data: T              # 反序列化后的数据（类型安全）
    raw_data: bytes      # 原始响应数据（字节）
```

#### 3.2 使用示例

```python
# 通常通过 api_client.response_deserialize() 获得
from immich_python_sdk import ApiClient, Configuration, SearchApi, SmartSearchDto

config = Configuration(host='...')
config.api_key['api_key'] = '...'
client = ApiClient(config)
search_api = SearchApi(client)

# 调用 API（内部会返回 ApiResponse）
result = search_api.search_smart(
    smart_search_dto=SmartSearchDto(query='red clothes')
)
# result 是 SearchResponseDto 对象（不是 ApiResponse）

# 如果需要完整的响应信息，使用 _with_http_info 方法
api_response = search_api.search_smart_with_http_info(
    smart_search_dto=SmartSearchDto(query='red clothes')
)
# api_response 是 ApiResponse[SearchResponseDto] 对象

# 访问响应信息
print(f"状态码: {api_response.status_code}")
print(f"响应头: {api_response.headers}")
print(f"数据: {api_response.data}")
print(f"原始数据: {api_response.raw_data}")
```

#### 3.3 实际应用场景

```python
# 场景1：获取响应头信息（如分页信息）
api_response = search_api.search_smart_with_http_info(...)

# 检查是否有下一页
link_header = api_response.headers.get('Link', '')
has_next = 'rel="next"' in link_header

# 场景2：记录原始响应（用于调试）
api_response = search_api.search_smart_with_http_info(...)

# 保存原始响应
with open('response.json', 'wb') as f:
    f.write(api_response.raw_data)

# 场景3：检查响应状态
api_response = search_api.search_smart_with_http_info(...)

if api_response.status_code == 200:
    data = api_response.data
    print(f"成功: {data.assets.total} 个结果")
elif api_response.status_code == 401:
    print("认证失败")
elif api_response.status_code == 429:
    print("请求过于频繁，需要限流")

# 场景4：类型安全的响应处理
from immich_python_sdk.models import SearchResponseDto

api_response: ApiResponse[SearchResponseDto] = search_api.search_smart_with_http_info(...)

# TypeScript 风格的类型检查
if isinstance(api_response.data, SearchResponseDto):
    # IDE 会提供自动补全
    total = api_response.data.assets.total
    items = api_response.data.assets.items
```

---

## 4. rest.py - 底层 HTTP 客户端

### 作用
基于 `urllib3` 的底层 HTTP 客户端，负责实际的网络请求。

### 核心功能

#### 4.1 RESTClientObject 类

```python
from immich_python_sdk.rest import RESTClientObject
from immich_python_sdk import Configuration

config = Configuration(host='...')
rest_client = RESTClientObject(config)

# 发送 HTTP 请求
response = rest_client.request(
    method='POST',
    url='http://127.0.0.1:2283/api/search/smart',
    headers={'x-api-key': '...', 'Content-Type': 'application/json'},
    body='{"query": "red clothes"}',  # JSON 字符串
    _request_timeout=30
)
# 返回: RESTResponse 对象
```

#### 4.2 RESTResponse 类

```python
from immich_python_sdk.rest import RESTResponse

# RESTResponse 是 urllib3.HTTPResponse 的包装
response: RESTResponse = rest_client.request(...)

# 读取响应数据
response.read()  # 必须调用，否则 response.data 为 None
data = response.data  # bytes 类型

# 获取状态信息
status = response.status  # HTTP 状态码
reason = response.reason  # HTTP 状态原因

# 获取响应头
headers = response.getheaders()  # 字典
content_type = response.getheader('Content-Type')  # 单个头
```

#### 4.3 支持的请求方法

```python
# RESTClientObject.request() 支持以下方法：
methods = ['GET', 'HEAD', 'DELETE', 'POST', 'PUT', 'PATCH', 'OPTIONS']

# 示例：GET 请求
response = rest_client.request(
    method='GET',
    url='http://127.0.0.1:2283/api/assets/123',
    headers={'x-api-key': '...'}
)

# 示例：POST 请求（JSON）
response = rest_client.request(
    method='POST',
    url='http://127.0.0.1:2283/api/search/smart',
    headers={
        'x-api-key': '...',
        'Content-Type': 'application/json'
    },
    body='{"query": "red clothes"}'
)

# 示例：POST 请求（表单）
response = rest_client.request(
    method='POST',
    url='http://127.0.0.1:2283/api/upload',
    headers={'x-api-key': '...'},
    post_params=[
        ('file', ('image.jpg', file_data, 'image/jpeg'))
    ]
)
```

### 实际应用场景

```python
# 场景1：直接使用底层客户端（绕过高级 API）
from immich_python_sdk.rest import RESTClientObject
from immich_python_sdk import Configuration
import json

config = Configuration(host='http://127.0.0.1:2283/api')
config.api_key['api_key'] = 'your-key'
rest_client = RESTClientObject(config)

# 构建请求
url = f"{config.host}/search/smart"
headers = {
    'x-api-key': config.api_key['api_key'],
    'Content-Type': 'application/json'
}
body = json.dumps({'query': 'red clothes', 'size': 10})

# 发送请求
response = rest_client.request('POST', url, headers=headers, body=body)
response.read()

# 解析响应
if response.status == 200:
    data = json.loads(response.data.decode('utf-8'))
    print(f"找到 {data['assets']['total']} 个结果")
else:
    print(f"错误: {response.status} - {response.reason}")

# 场景2：文件下载（流式处理）
response = rest_client.request(
    'GET',
    f"{config.host}/assets/{asset_id}/original",
    headers={'x-api-key': config.api_key['api_key']}
)

# 流式读取（对于大文件）
with open('image.jpg', 'wb') as f:
    while True:
        chunk = response.read(8192)  # 8KB 块
        if not chunk:
            break
        f.write(chunk)

# 场景3：自定义超时和重试
config.retries = 5  # 重试次数
rest_client = RESTClientObject(config)

response = rest_client.request(
    'GET',
    url,
    headers=headers,
    _request_timeout=(5, 30)  # (连接超时, 读取超时)
)
```

---

## 5. exceptions.py - 异常处理

### 作用
提供结构化的异常处理，包括 HTTP 状态码异常和数据类型异常。

### 核心功能

#### 5.1 异常类层次结构

```
OpenApiException (基类)
├── ApiTypeError (类型错误)
├── ApiValueError (值错误)
├── ApiAttributeError (属性错误)
├── ApiKeyError (键错误)
└── ApiException (API 异常)
    ├── BadRequestException (400)
    ├── UnauthorizedException (401)
    ├── ForbiddenException (403)
    ├── NotFoundException (404)
    ├── ConflictException (409)
    ├── UnprocessableEntityException (422)
    └── ServiceException (500-599)
```

#### 5.2 使用示例

```python
from immich_python_sdk import SearchApi, SmartSearchDto
from immich_python_sdk.exceptions import (
    ApiException,
    UnauthorizedException,
    NotFoundException,
    BadRequestException
)

try:
    result = search_api.search_smart(
        smart_search_dto=SmartSearchDto(query='red clothes')
    )
except UnauthorizedException as e:
    print(f"认证失败: {e.status} - {e.reason}")
    print(f"响应体: {e.body}")
    # 可能需要重新登录或刷新 token
except NotFoundException as e:
    print(f"资源未找到: {e.status}")
except BadRequestException as e:
    print(f"请求错误: {e.body}")
    # 可能是参数错误
except ApiException as e:
    print(f"API 错误: {e.status} - {e.reason}")
    print(f"响应头: {e.headers}")
    print(f"响应体: {e.body}")
except Exception as e:
    print(f"其他错误: {e}")
```

#### 5.3 异常对象属性

```python
try:
    result = search_api.search_smart(...)
except ApiException as e:
    # 访问异常信息
    status = e.status          # HTTP 状态码
    reason = e.reason          # HTTP 状态原因
    body = e.body             # 响应体（字符串）
    data = e.data             # 反序列化后的响应数据
    headers = e.headers       # 响应头（字典）
    
    # 打印完整错误信息
    print(str(e))  # 包含状态码、原因、响应头、响应体
```

### 实际应用场景

```python
# 场景1：优雅的错误处理
from immich_python_sdk.exceptions import (
    UnauthorizedException,
    NotFoundException,
    ServiceException
)

def search_with_retry(search_api, query, max_retries=3):
    for attempt in range(max_retries):
        try:
            result = search_api.search_smart(
                smart_search_dto=SmartSearchDto(query=query)
            )
            return result
        except UnauthorizedException:
            # 认证失败，需要重新登录
            print("认证失败，尝试重新登录...")
            # 重新登录逻辑
            if attempt < max_retries - 1:
                continue
            raise
        except ServiceException as e:
            # 服务器错误，可以重试
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 指数退避
                print(f"服务器错误，{wait_time}秒后重试...")
                time.sleep(wait_time)
                continue
            raise
        except NotFoundException:
            # 资源不存在，不需要重试
            return None

# 场景2：详细的错误日志
import logging
from immich_python_sdk.exceptions import ApiException

logger = logging.getLogger(__name__)

try:
    result = search_api.search_smart(...)
except ApiException as e:
    logger.error(
        f"API 调用失败",
        extra={
            'status': e.status,
            'reason': e.reason,
            'headers': e.headers,
            'body': e.body,
            'data': e.data
        }
    )
    raise

# 场景3：错误分类处理
def handle_api_error(e: ApiException):
    if e.status == 401:
        return "需要重新登录"
    elif e.status == 403:
        return "没有权限访问此资源"
    elif e.status == 404:
        return "资源不存在"
    elif e.status == 429:
        return "请求过于频繁，请稍后再试"
    elif 500 <= e.status < 600:
        return "服务器错误，请稍后再试"
    else:
        return f"未知错误: {e.status}"

try:
    result = search_api.search_smart(...)
except ApiException as e:
    user_message = handle_api_error(e)
    print(user_message)
```

---

## 综合使用示例

### 完整的工作流程

```python
from immich_python_sdk import (
    Configuration,
    ApiClient,
    SearchApi,
    SmartSearchDto
)
from immich_python_sdk.exceptions import ApiException
from immich_python_sdk.api_response import ApiResponse

# 1. 创建配置
config = Configuration(host='http://127.0.0.1:2283/api')
config.api_key['api_key'] = 'your-api-key'

# 2. 创建客户端
client = ApiClient(config)

# 3. 创建 API 实例
search_api = SearchApi(client)

# 4. 调用 API（方式1：简单调用）
try:
    result = search_api.search_smart(
        smart_search_dto=SmartSearchDto(query='red clothes', size=10)
    )
    print(f"找到 {result.assets.total} 个结果")
except ApiException as e:
    print(f"错误: {e}")

# 5. 调用 API（方式2：获取完整响应信息）
try:
    api_response: ApiResponse = search_api.search_smart_with_http_info(
        smart_search_dto=SmartSearchDto(query='red clothes', size=10)
    )
    
    # 访问响应数据
    print(f"状态码: {api_response.status_code}")
    print(f"响应头: {api_response.headers}")
    print(f"数据: {api_response.data}")
    print(f"原始数据长度: {len(api_response.raw_data)} bytes")
    
    # 访问业务数据
    search_result = api_response.data
    print(f"资产总数: {search_result.assets.total}")
    print(f"返回数量: {search_result.assets.count}")
    
except ApiException as e:
    print(f"错误: {e.status} - {e.reason}")
    print(f"响应体: {e.body}")
```

---

## 总结

### 各文件的作用

1. **configuration.py**: 配置管理，设置认证、URL、SSL 等
2. **api_client.py**: 核心客户端，处理请求/响应序列化和反序列化
3. **api_response.py**: 响应对象封装，提供类型安全的响应数据访问
4. **rest.py**: 底层 HTTP 客户端，基于 urllib3 的实际网络请求
5. **exceptions.py**: 异常处理，提供结构化的错误信息

### 使用建议

1. **日常使用**: 直接使用高级 API（如 `SearchApi`），不需要直接操作这些核心文件
2. **自定义需求**: 如果需要自定义请求处理，可以使用 `ApiClient` 和 `RESTClientObject`
3. **错误处理**: 始终使用 `exceptions` 模块中的异常类进行错误处理
4. **响应信息**: 如果需要完整的响应信息（状态码、响应头等），使用 `_with_http_info` 方法

### 最佳实践

```python
# ✅ 推荐：使用高级 API
search_api = SearchApi(client)
result = search_api.search_smart(...)

# ⚠️ 高级用法：需要完整响应信息
api_response = search_api.search_smart_with_http_info(...)

# ⚠️ 高级用法：自定义请求
method, url, headers, body, _ = client.param_serialize(...)
response = client.call_api(method, url, headers, body)
api_response = client.response_deserialize(response, ...)

# ❌ 不推荐：直接使用底层 REST 客户端（除非有特殊需求）
rest_client = RESTClientObject(config)
response = rest_client.request(...)
```
