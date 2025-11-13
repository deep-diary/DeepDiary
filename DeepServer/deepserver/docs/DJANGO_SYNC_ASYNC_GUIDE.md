# Django 同步 vs 异步开发指南

## 📚 目录
1. [基本概念](#基本概念)
2. [何时使用同步](#何时使用同步)
3. [何时使用异步](#何时使用异步)
4. [混合使用策略](#混合使用策略)
5. [实际应用场景](#实际应用场景)
6. [性能对比](#性能对比)
7. [迁移建议](#迁移建议)

---

## 基本概念

### 同步（Synchronous）
- **WSGI 服务器**：Gunicorn, uWSGI
- **特点**：一个请求占用一个线程/进程，阻塞式处理
- **适用**：CPU 密集型、简单 CRUD 操作

### 异步（Asynchronous）
- **ASGI 服务器**：Uvicorn, Daphne, Hypercorn
- **特点**：单线程处理多个请求，非阻塞式处理
- **适用**：I/O 密集型、WebSocket、长连接

---

## 何时使用同步

### ✅ 推荐使用同步的场景

#### 1. **传统 CRUD 应用**
```python
# views.py - 同步视图
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required

@login_required
def user_profile(request, user_id):
    user = get_object_or_404(User, id=user_id)
    return render(request, 'users/profile.html', {'user': user})
```

**原因**：
- Django ORM 同步 API 成熟稳定
- 代码简单易维护
- 性能足够（数据库查询通常很快）

#### 2. **Django Admin**
```python
# admin.py - 同步
from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'date_joined']
```

**原因**：
- Django Admin 完全基于同步
- 功能完整，无需异步

#### 3. **表单处理**
```python
# forms.py - 同步
from django import forms
from django.contrib.auth.forms import UserCreationForm

class CustomUserForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user
```

**原因**：
- 表单验证和处理逻辑简单
- 同步代码更直观

#### 4. **文件上传/下载**
```python
# views.py - 同步
from django.http import FileResponse
from django.views.decorators.cache import cache_control

@cache_control(max_age=3600)
def download_file(request, file_id):
    file_obj = get_object_or_404(File, id=file_id)
    return FileResponse(file_obj.file.open(), as_attachment=True)
```

**原因**：
- 文件 I/O 操作简单直接
- 同步处理更易控制

---

## 何时使用异步

### ✅ 推荐使用异步的场景

#### 1. **高并发 I/O 密集型操作**
```python
# views.py - 异步视图
from django.http import JsonResponse
from asgiref.sync import sync_to_async
import httpx

async def fetch_external_data(request):
    """并发请求多个外部 API"""
    async with httpx.AsyncClient() as client:
        # 并发执行多个请求
        results = await asyncio.gather(
            client.get('https://api1.example.com/data'),
            client.get('https://api2.example.com/data'),
            client.get('https://api3.example.com/data'),
        )
    return JsonResponse({'results': [r.json() for r in results]})
```

**优势**：
- 可以同时处理多个外部 API 请求
- 显著提升性能（从串行变为并行）

#### 2. **WebSocket 连接**
```python
# consumers.py - ASGI 应用
from channels.generic.websocket import AsyncWebsocketConsumer
import json

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message
            }
        )
```

**原因**：
- WebSocket 需要长连接
- 异步是唯一选择

#### 3. **实时数据推送**
```python
# views.py - Server-Sent Events (SSE)
from django.http import StreamingHttpResponse
import asyncio

async def stream_data(request):
    async def event_stream():
        while True:
            data = await fetch_latest_data()
            yield f"data: {json.dumps(data)}\n\n"
            await asyncio.sleep(1)
    
    response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    return response
```

#### 4. **批量数据处理**
```python
# tasks.py - 异步批量处理
import asyncio
from asgiref.sync import sync_to_async

async def process_batch_async(items):
    """异步批量处理"""
    tasks = [process_item_async(item) for item in items]
    results = await asyncio.gather(*tasks)
    return results

async def process_item_async(item):
    # 模拟 I/O 操作
    await asyncio.sleep(0.1)
    return process_item(item)
```

---

## 混合使用策略

### 🔄 在同步视图中调用异步代码

```python
# views.py - 混合使用
from django.http import JsonResponse
from asgiref.sync import async_to_sync
import httpx

def sync_view_with_async(request):
    """同步视图中使用异步代码"""
    async def fetch_data():
        async with httpx.AsyncClient() as client:
            response = await client.get('https://api.example.com/data')
            return response.json()
    
    # 在同步上下文中运行异步函数
    data = async_to_sync(fetch_data)()
    return JsonResponse(data)
```

### 🔄 在异步视图中调用同步代码

```python
# views.py - 异步视图中使用同步 ORM
from django.http import JsonResponse
from asgiref.sync import sync_to_async
from .models import User

async def async_view_with_sync_orm(request):
    """异步视图中使用同步 ORM"""
    # 将同步 ORM 查询包装为异步
    get_user = sync_to_async(User.objects.get)
    user = await get_user(id=1)
    
    return JsonResponse({
        'username': user.username,
        'email': user.email
    })
```

### ⚠️ 注意事项

1. **避免在异步视图中直接使用同步 ORM**
   ```python
   # ❌ 错误：会阻塞事件循环
   async def bad_view(request):
       user = User.objects.get(id=1)  # 阻塞！
       return JsonResponse({'user': user.username})
   
   # ✅ 正确：使用 sync_to_async
   async def good_view(request):
       get_user = sync_to_async(User.objects.get)
       user = await get_user(id=1)
       return JsonResponse({'user': user.username})
   ```

2. **数据库连接池配置**
   ```python
   # settings.py
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'CONN_MAX_AGE': 0,  # 异步模式下设为 0
           'OPTIONS': {
               'connect_timeout': 10,
           }
       }
   }
   ```

---

## 实际应用场景

### 场景 1：API 聚合服务

**需求**：聚合多个外部 API 的数据

```python
# ✅ 使用异步
import httpx
from django.http import JsonResponse

async def aggregate_apis(request):
    async with httpx.AsyncClient(timeout=10.0) as client:
        # 并发请求多个 API
        results = await asyncio.gather(
            client.get('https://api1.com/data'),
            client.get('https://api2.com/data'),
            client.get('https://api3.com/data'),
            return_exceptions=True
        )
    
    data = []
    for result in results:
        if isinstance(result, httpx.Response):
            data.append(result.json())
        else:
            data.append({'error': str(result)})
    
    return JsonResponse({'results': data})
```

**性能提升**：从 3 秒（串行）降到 1 秒（并行）

### 场景 2：用户注册（发送邮件）

**需求**：用户注册后发送验证邮件

```python
# ✅ 使用 Celery（推荐）或异步视图
from celery import shared_task
from django.core.mail import send_mail

@shared_task
def send_verification_email(user_id):
    user = User.objects.get(id=user_id)
    send_mail(
        '验证您的邮箱',
        '验证链接...',
        'noreply@example.com',
        [user.email],
    )

# views.py
def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # 异步发送邮件，不阻塞请求
            send_verification_email.delay(user.id)
            return redirect('registration_success')
```

**原因**：
- 邮件发送可能较慢（网络 I/O）
- 使用 Celery 避免阻塞用户请求
- 更可靠（支持重试、队列）

### 场景 3：实时聊天

**需求**：WebSocket 实时通信

```python
# ✅ 必须使用异步（ASGI）
from channels.generic.websocket import AsyncWebsocketConsumer

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # 异步连接处理
        await self.accept()
    
    async def receive(self, text_data):
        # 异步消息处理
        await self.send(text_data=text_data)
```

---

## 性能对比

### 同步 vs 异步性能测试

```python
# 测试场景：并发请求 100 个外部 API

# 同步版本（串行）
def sync_fetch():
    for url in urls:
        response = requests.get(url)  # 阻塞
        results.append(response.json())
# 耗时：~100 秒（假设每个请求 1 秒）

# 异步版本（并行）
async def async_fetch():
    async with httpx.AsyncClient() as client:
        tasks = [client.get(url) for url in urls]
        responses = await asyncio.gather(*tasks)
        results = [r.json() for r in responses]
# 耗时：~1 秒（并发执行）
```

### 资源消耗对比

| 特性 | 同步（WSGI） | 异步（ASGI） |
|------|-------------|-------------|
| 内存占用 | 较高（每个请求一个线程） | 较低（单线程事件循环） |
| CPU 使用 | 中等 | 较低 |
| 并发能力 | 受线程数限制 | 高（数千并发） |
| 适用场景 | CPU 密集型、简单 CRUD | I/O 密集型、WebSocket |

---

## 迁移建议

### 当前项目分析

根据你的项目配置：

```python
# config/settings/base.py
WSGI_APPLICATION = "config.wsgi.application"  # 当前使用 WSGI
```

**建议**：

1. **保持同步为主**（当前策略）
   - 大部分视图使用同步
   - Django ORM 同步 API
   - Django Admin 同步

2. **异步用于特定场景**
   - 外部 API 调用
   - WebSocket（如果未来需要）
   - 实时数据推送

3. **使用 Celery 处理后台任务**
   - 邮件发送
   - 文件处理
   - 定时任务

### 迁移步骤

#### 步骤 1：评估需求
- 是否有高并发 I/O 操作？
- 是否需要 WebSocket？
- 是否有实时推送需求？

#### 步骤 2：渐进式迁移
```python
# 1. 先添加 ASGI 支持（不破坏现有代码）
# config/asgi.py
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django_asgi_app = get_asgi_application()

# 2. 在 settings.py 中添加
ASGI_APPLICATION = "config.asgi.application"

# 3. 逐步将特定视图改为异步
```

#### 步骤 3：使用混合模式
```python
# 大部分视图保持同步
def user_list(request):
    users = User.objects.all()
    return render(request, 'users/list.html', {'users': users})

# 特定视图使用异步
async def api_aggregate(request):
    # 异步处理
    pass
```

---

## 最佳实践总结

### ✅ 推荐做法

1. **默认使用同步**
   - 简单、稳定、易维护
   - Django ORM 同步 API 成熟

2. **异步用于特定场景**
   - 高并发 I/O 操作
   - WebSocket
   - 实时推送

3. **使用 Celery 处理后台任务**
   - 长时间运行的任务
   - 定时任务
   - 邮件发送

4. **混合使用**
   - 在同步视图中调用异步代码（使用 `async_to_sync`）
   - 在异步视图中使用同步 ORM（使用 `sync_to_async`）

### ❌ 避免的做法

1. **不要过度使用异步**
   - 简单的 CRUD 操作不需要异步
   - 异步代码更复杂，调试困难

2. **不要在异步视图中直接使用同步 ORM**
   - 会阻塞事件循环
   - 必须使用 `sync_to_async` 包装

3. **不要混用同步和异步中间件**
   - 可能导致性能问题

---

## 参考资源

- [Django 异步支持文档](https://docs.djangoproject.com/en/stable/topics/async/)
- [ASGI 规范](https://asgi.readthedocs.io/)
- [Celery 文档](https://docs.celeryq.dev/)
- [Django Channels 文档](https://channels.readthedocs.io/)

---

## 快速决策树

```
需要处理请求
│
├─ 简单 CRUD 操作？
│  └─ 是 → 使用同步 ✅
│
├─ 需要 WebSocket？
│  └─ 是 → 使用异步 ✅
│
├─ 高并发 I/O 操作？
│  └─ 是 → 使用异步 ✅
│
├─ 长时间运行的任务？
│  └─ 是 → 使用 Celery ✅
│
└─ 其他情况
   └─ 使用同步 ✅
```

---

**总结**：对于你的项目，建议**保持同步为主，异步为辅**的策略。大部分功能使用同步，只在特定场景（如外部 API 调用、WebSocket）使用异步。

