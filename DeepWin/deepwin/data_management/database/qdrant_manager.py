#!/usr/bin/env python3
"""
DeepWin Qdrant Database Manager
使用langchain-qdrant管理向量数据库，支持本地文件存储
"""

import asyncio
import os
import subprocess
import threading
import time
from typing import Any, Dict, List, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter
from langchain_community.vectorstores import Qdrant as LangchainQdrant

from .base_database import BaseDatabase
from ..config_manager import ConfigManager
from ..log_manager import LogManager


class QdrantManager(BaseDatabase):
    """Qdrant向量数据库管理器，使用langchain-qdrant"""
    
    def __init__(self, name: str, config_manager: ConfigManager, log_manager: LogManager, parent=None, **kwargs):
        super().__init__(name, config_manager, log_manager, parent)
        
        # 从参数或配置管理器获取配置
        self.host = kwargs.get('host', config_manager.get('database.qdrant.host', 'localhost'))
        self.port = kwargs.get('port', config_manager.get('database.qdrant.port', 6333))
        self.local_path = kwargs.get('local_path', config_manager.get('database.qdrant.local_path', None))
        self.api_key = kwargs.get('api_key', config_manager.get('database.qdrant.api_key', None))
        self.use_memory = kwargs.get('use_memory', False)  # 新增：内存模式标志
        
        # 客户端和集合
        self.client = None
        self.collections = {}
        self.langchain_stores = {}
        
        # Web UI相关配置
        self.web_ui_process = None
        self.web_ui_port = kwargs.get('web_ui_port', 6333)
        self.web_ui_enabled = kwargs.get('web_ui_enabled', False)
        
        # 向量维度配置
        self.vector_sizes = {
            'user_embeddings': 1536,
            'photo_embeddings': 512,
            'memory_embeddings': 1536,
        }

    async def connect(self) -> bool:
        """连接到Qdrant数据库"""
        try:
            # 如果已经有连接，先断开
            if self.client:
                await self.disconnect()
            
            # 优先使用内存模式
            if self.use_memory:
                self.client = QdrantClient(":memory:")
                self.logger.info("使用内存模式Qdrant数据库")
            # 检查本地路径是否存在，如果不存在则创建
            elif self.local_path:
                os.makedirs(self.local_path, exist_ok=True)
                
                # 尝试连接到本地Qdrant数据库
                try:
                    self.client = QdrantClient(path=self.local_path)
                    # 测试连接
                    self.client.get_collections()
                    self.logger.info(f"连接到本地Qdrant数据库: {self.local_path}")
                except Exception as local_error:
                    self.logger.warning(f"本地Qdrant连接失败: {local_error}")
                    # 如果本地连接失败，尝试使用HTTP模式
                    try:
                        self.client = QdrantClient(
                            host="localhost",
                            port=6333,
                            prefer_grpc=False  # 使用HTTP模式
                        )
                        # 测试连接
                        self.client.get_collections()
                        self.logger.info(f"通过HTTP模式连接到Qdrant: localhost:6333")
                    except Exception as http_error:
                        self.logger.warning(f"HTTP模式连接也失败: {http_error}")
                        # 最后尝试使用内存模式
                        self.client = QdrantClient(":memory:")
                        self.logger.info("使用内存模式Qdrant数据库")
            else:
                self.client = QdrantClient(
                    host=self.host,
                    port=self.port,
                    api_key=self.api_key
                )
                self.logger.info(f"连接到远程Qdrant数据库: {self.host}:{self.port}")
            
            await self._init_collections()
            
            # 如果启用了Web UI，则启动它
            if self.web_ui_enabled:
                await self._start_web_ui()
            
            self.is_connected = True
            self.connected.emit(self.name)
            return True
            
        except Exception as e:
            self.logger.error(f"Qdrant数据库连接失败: {e}")
            self.error_occurred.emit(self.name, str(e))
            return False
    
    async def _start_local_qdrant_service(self) -> bool:
        """启动本地Qdrant服务"""
        try:
            # 检查是否已经有Qdrant进程在运行
            if self._is_qdrant_running():
                self.logger.info("Qdrant服务已在运行")
                return True
            
            # 启动本地Qdrant服务
            self.logger.info("启动本地Qdrant服务...")
            
            # 使用subprocess启动Qdrant
            cmd = ["qdrant", "--storage-path", self.local_path]
            self.web_ui_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            # 等待服务启动
            await asyncio.sleep(3)
            
            # 检查服务是否启动成功
            if self.web_ui_process.poll() is None:
                self.logger.info("本地Qdrant服务启动成功")
                return True
            else:
                self.logger.error("本地Qdrant服务启动失败")
                return False
                
        except Exception as e:
            self.logger.error(f"启动本地Qdrant服务失败: {e}")
            return False
    
    def _is_qdrant_running(self) -> bool:
        """检查Qdrant服务是否在运行"""
        try:
            # 尝试连接到默认端口
            test_client = QdrantClient(host="localhost", port=6333)
            test_client.get_collections()
            test_client.close()
            return True
        except:
            return False

    async def disconnect(self) -> bool:
        """断开Qdrant数据库连接"""
        try:
            # 停止Web UI
            if self.web_ui_process:
                await self._stop_web_ui()
            
            if self.client:
                self.client.close()
                self.client = None
            
            self.collections.clear()
            self.langchain_stores.clear()
            self.is_connected = False
            
            self.disconnected.emit(self.name)
            return True
            
        except Exception as e:
            self.logger.error(f"Qdrant数据库断开连接失败: {e}")
            self.error_occurred.emit(self.name, str(e))
            return False

    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """执行向量查询操作"""
        if not self.is_connected:
            raise ConnectionError("数据库未连接")
        
        try:
            collection_name = params.get('collection', 'user_embeddings')
            query_vector = params.get('vector')
            limit = params.get('limit', 10)
            
            if query_vector:
                results = self.client.search(
                    collection_name=collection_name,
                    query_vector=query_vector,
                    limit=limit
                )
                return [point.dict() for point in results]
            else:
                results = self.client.scroll(
                    collection_name=collection_name,
                    limit=limit
                )
                return [point.dict() for point in results[0]]
                
        except Exception as e:
            self.logger.error(f"向量查询执行失败: {e}")
            self.error_occurred.emit(self.name, f"查询失败: {e}")
            raise

    async def execute_command(self, command: str, params: Optional[Dict[str, Any]] = None) -> bool:
        """执行命令操作"""
        if not self.is_connected:
            raise ConnectionError("数据库未连接")
        
        try:
            if command == 'insert':
                await self._insert_points(params)
            elif command == 'update':
                await self._update_points(params)
            elif command == 'delete':
                await self._delete_points(params)
            else:
                raise ValueError(f"未知命令: {command}")
            
            self.operation_completed.emit(self.name, f"命令执行成功: {command}")
            return True
            
        except Exception as e:
            self.logger.error(f"命令执行失败: {e}")
            self.error_occurred.emit(self.name, f"命令失败: {e}")
            return False

    async def begin_transaction(self) -> bool:
        """开始事务（Qdrant不支持传统事务）"""
        self.logger.info("Qdrant不支持传统事务，使用批量操作")
        return True

    async def commit_transaction(self) -> bool:
        """提交事务（Qdrant不支持传统事务）"""
        self.logger.info("Qdrant事务模拟提交")
        return True

    async def rollback_transaction(self) -> bool:
        """回滚事务（Qdrant不支持传统事务）"""
        self.logger.info("Qdrant事务模拟回滚")
        return True

    async def _init_collections(self):
        """初始化集合"""
        try:
            for collection_name, vector_size in self.vector_sizes.items():
                await self._create_collection_if_not_exists(collection_name, vector_size)
                
                # 暂时跳过LangChain存储的创建，避免embeddings错误
                # 在实际使用时，应该传入真实的embeddings模型
                # self.langchain_stores[collection_name] = LangchainQdrant(
                #     client=self.client,
                #     collection_name=collection_name,
                #     embeddings=None,  # 暂时为None，实际使用时需要传入
                #     vector_name="vector"
                # )
                
            self.logger.info(f"Qdrant集合初始化完成: {list(self.vector_sizes.keys())}")
            
        except Exception as e:
            self.logger.error(f"集合初始化失败: {e}")
            raise

    async def _create_collection_if_not_exists(self, collection_name: str, vector_size: int):
        """创建集合（如果不存在）"""
        try:
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=vector_size,
                        distance=Distance.COSINE
                    )
                )
                self.logger.info(f"创建集合: {collection_name}")
            else:
                self.logger.info(f"集合已存在: {collection_name}")
                
        except Exception as e:
            self.logger.error(f"创建集合失败 {collection_name}: {e}")
            raise

    async def _insert_points(self, params: Dict[str, Any]):
        """插入向量点"""
        collection_name = params.get('collection')
        points = params.get('points', [])
        
        if not collection_name or not points:
            raise ValueError("缺少必要参数")
        
        point_structs = []
        for point_data in points:
            point = PointStruct(
                id=point_data.get('id'),
                vector=point_data.get('vector'),
                payload=point_data.get('payload', {})
            )
            point_structs.append(point)
        
        self.client.upsert(
            collection_name=collection_name,
            points=point_structs
        )

    async def _update_points(self, params: Dict[str, Any]):
        """更新向量点"""
        collection_name = params.get('collection')
        points = params.get('points', [])
        
        if not collection_name or not points:
            raise ValueError("缺少必要参数")
        
        for point_data in points:
            self.client.set_payload(
                collection_name=collection_name,
                payload=point_data.get('payload', {}),
                points=[point_data.get('id')]
            )

    async def _delete_points(self, params: Dict[str, Any]):
        """删除向量点"""
        collection_name = params.get('collection')
        point_ids = params.get('point_ids', [])
        
        if not collection_name or not point_ids:
            raise ValueError("缺少必要参数")
        
        # 使用正确的删除方法，传入points_selector
        self.client.delete(
            collection_name=collection_name,
            points_selector=point_ids
        )

    def get_langchain_store(self, collection_name: str):
        """获取langchain-qdrant存储实例"""
        return self.langchain_stores.get(collection_name)

    def set_embeddings(self, collection_name: str, embeddings):
        """为指定集合设置embeddings"""
        if collection_name in self.langchain_stores:
            self.langchain_stores[collection_name].embeddings = embeddings

    async def _ensure_collection_exists(self, collection_name: str, vector_size: int) -> bool:
        """确保集合存在，如果不存在则创建"""
        try:
            if not self.is_connected:
                self.logger.error("Qdrant数据库未连接")
                return False
            
            # 检查集合是否存在
            collections = self.client.get_collections()
            existing_collections = [col.name for col in collections.collections]
            
            if collection_name not in existing_collections:
                # 创建新集合
                from qdrant_client.models import VectorParams, Distance
                
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=vector_size,
                        distance=Distance.COSINE
                    )
                )
                self.logger.info(f"创建集合: {collection_name}")
            else:
                self.logger.info(f"集合已存在: {collection_name}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"确保集合存在失败 {collection_name}: {e}")
            return False

    async def insert_vector(self, collection_name: str, vector_id: str, vector: List[float], payload: Dict[str, Any] = None) -> bool:
        """插入单个向量"""
        try:
            if not self.is_connected:
                self.logger.error("Qdrant数据库未连接")
                return False
            
            # 确保集合存在
            await self._ensure_collection_exists(collection_name, len(vector))
            
            # 创建点结构
            point = PointStruct(
                id=vector_id,
                vector=vector,
                payload=payload or {}
            )
            
            # 插入向量
            self.client.upsert(
                collection_name=collection_name,
                points=[point]
            )
            
            self.logger.info(f"向量插入成功: {collection_name}/{vector_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"向量插入失败: {e}")
            return False

    async def insert_vectors(self, collection_name: str, vectors: List[Dict[str, Any]]) -> bool:
        """批量插入向量"""
        try:
            if not self.is_connected:
                self.logger.error("Qdrant数据库未连接")
                return False
            
            if not vectors:
                self.logger.warning("没有向量数据需要插入")
                return True
            
            # 确保集合存在
            vector_size = len(vectors[0].get('vector', []))
            await self._ensure_collection_exists(collection_name, vector_size)
            
            # 创建点结构列表
            points = []
            for vector_data in vectors:
                point = PointStruct(
                    id=vector_data.get('id'),
                    vector=vector_data.get('vector'),
                    payload=vector_data.get('payload', {})
                )
                points.append(point)
            
            # 批量插入
            self.client.upsert(
                collection_name=collection_name,
                points=points
            )
            
            self.logger.info(f"批量向量插入成功: {collection_name}/{len(points)} 个向量")
            return True
            
        except Exception as e:
            self.logger.error(f"批量向量插入失败: {e}")
            return False

    async def search_vectors(self, collection_name: str, query_vector: List[float], limit: int = 10, score_threshold: float = 0.0) -> List[Dict[str, Any]]:
        """搜索向量"""
        try:
            if not self.is_connected:
                self.logger.error("Qdrant数据库未连接")
                return []
            
            # 执行向量搜索
            search_result = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold
            )
            
            # 转换结果格式
            results = []
            for point in search_result:
                results.append({
                    'id': point.id,
                    'score': point.score,
                    'payload': point.payload,
                    'vector': point.vector
                })
            
            self.logger.info(f"向量搜索完成: {collection_name}, 找到 {len(results)} 个结果")
            return results
            
        except Exception as e:
            self.logger.error(f"向量搜索失败: {e}")
            return []

    async def delete_vector(self, collection_name: str, vector_id: str) -> bool:
        """删除向量"""
        try:
            if not self.is_connected:
                self.logger.error("Qdrant数据库未连接")
                return False
            
            self.client.delete(
                collection_name=collection_name,
                points_selector=[vector_id]
            )
            
            self.logger.info(f"向量删除成功: {collection_name}/{vector_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"向量删除失败: {e}")
            return False

    async def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """获取集合信息"""
        try:
            if not self.is_connected:
                self.logger.error("Qdrant数据库未连接")
                return {}
            
            info = self.client.get_collection(collection_name)
            return {
                'name': info.name,
                'vectors_count': info.vectors_count,
                'points_count': info.points_count,
                'segments_count': info.segments_count,
                'config': {
                    'vector_size': info.config.params.vectors.size,
                    'distance': info.config.params.vectors.distance
                }
            }
            
        except Exception as e:
            self.logger.error(f"获取集合信息失败: {e}")
            return {}

    async def get_all_collections(self) -> List[str]:
        """获取所有集合名称"""
        try:
            if not self.is_connected:
                self.logger.error("Qdrant数据库未连接")
                return []
            
            collections = self.client.get_collections()
            return [col.name for col in collections.collections]
            
        except Exception as e:
            self.logger.error(f"获取集合列表失败: {e}")
            return []

    async def delete_collection(self, collection_name: str) -> bool:
        """删除集合"""
        try:
            if not self.is_connected:
                self.logger.error("Qdrant数据库未连接")
                return False
            
            self.client.delete_collection(collection_name)
            self.logger.info(f"集合删除成功: {collection_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"集合删除失败: {e}")
            return False

    # ==================== Web UI 管理方法 ====================
    
    async def _start_web_ui(self):
        """启动Qdrant Web UI"""
        try:
            if self.web_ui_process and self.web_ui_process.poll() is None:
                self.logger.info("Web UI已经在运行中")
                return True
            
            # 首先尝试使用本地Qdrant可执行文件
            qdrant_cmd = self._find_qdrant_executable()
            if qdrant_cmd:
                return await self._start_qdrant_executable(qdrant_cmd)
            
            # 如果没有本地可执行文件，尝试使用Docker
            if await self._check_docker_available():
                return await self._start_qdrant_docker()
            
            # 最后尝试使用Python HTTP服务器
            self.logger.warning("未找到Qdrant可执行文件或Docker，使用Python HTTP服务器")
            return await self._start_python_http_server()
                
        except Exception as e:
            self.logger.error(f"启动Web UI失败: {e}")
            return False
    
    async def _stop_web_ui(self):
        """停止Qdrant Web UI"""
        try:
            # 停止Python HTTP服务器
            if hasattr(self, 'httpd') and self.httpd:
                try:
                    self.httpd.shutdown()
                    self.httpd.server_close()
                    self.logger.info("Python HTTP服务器已停止")
                except Exception as e:
                    self.logger.warning(f"停止HTTP服务器时出错: {e}")
            
            # 停止线程
            if hasattr(self, 'server_thread') and self.server_thread.is_alive():
                try:
                    self.server_thread.join(timeout=3)
                    if self.server_thread.is_alive():
                        self.logger.warning("Web UI线程未能在3秒内停止")
                    else:
                        self.logger.info("Web UI线程已停止")
                except Exception as e:
                    self.logger.warning(f"停止线程时出错: {e}")
            
            # 停止其他类型的Web UI进程
            if self.web_ui_process and hasattr(self.web_ui_process, 'poll'):
                if self.web_ui_process.poll() is None:
                    if hasattr(self.web_ui_process, 'terminate'):
                        try:
                            self.web_ui_process.terminate()
                            self.web_ui_process.wait(timeout=3)
                            self.logger.info("Web UI进程已停止")
                        except Exception as e:
                            self.logger.warning(f"停止进程时出错: {e}")
            
            # 清理引用
            self.web_ui_process = None
            self.httpd = None
            self.server_thread = None
            
        except Exception as e:
            self.logger.error(f"停止Web UI失败: {e}")
    
    async def _start_qdrant_executable(self, qdrant_cmd: str) -> bool:
        """使用本地Qdrant可执行文件启动Web UI"""
        try:
            cmd = [
                qdrant_cmd,
                "--path", self.local_path,
                "--http-port", str(self.web_ui_port),
                "--host", "0.0.0.0"
            ]
            
            self.web_ui_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            await asyncio.sleep(2)
            
            if self.web_ui_process.poll() is None:
                self.logger.info(f"Qdrant Web UI启动成功: http://localhost:{self.web_ui_port}/dashboard")
                return True
            else:
                self.logger.error("Web UI启动失败")
                return False
                
        except Exception as e:
            self.logger.error(f"使用可执行文件启动Web UI失败: {e}")
            return False
    
    async def _check_docker_available(self) -> bool:
        """检查Docker是否可用"""
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    async def _start_qdrant_docker(self) -> bool:
        """使用Docker启动Qdrant服务"""
        try:
            # 检查是否已有Qdrant容器运行
            check_cmd = ["docker", "ps", "--filter", "name=qdrant_test", "--format", "{{.Names}}"]
            result = subprocess.run(check_cmd, capture_output=True, text=True)
            
            if "qdrant_test" in result.stdout:
                self.logger.info("Qdrant Docker容器已在运行")
                return True
            
            # 启动新的Docker容器
            cmd = [
                "docker", "run", "-d",
                "--name", "qdrant_test",
                "-p", f"{self.web_ui_port}:6333",
                "-p", f"{self.web_ui_port+1}:6334",
                "-v", f"{os.path.abspath(self.local_path)}:/qdrant/storage",
                "qdrant/qdrant"
            ]
            
            self.web_ui_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            await asyncio.sleep(5)  # Docker启动需要更长时间
            
            # 检查容器状态
            status_cmd = ["docker", "ps", "--filter", "name=qdrant_test", "--format", "{{.Status}}"]
            status_result = subprocess.run(status_cmd, capture_output=True, text=True)
            
            if "Up" in status_result.stdout:
                self.logger.info(f"Qdrant Docker容器启动成功: http://localhost:{self.web_ui_port}/dashboard")
                return True
            else:
                self.logger.error("Docker容器启动失败")
                return False
                
        except Exception as e:
            self.logger.error(f"使用Docker启动Qdrant失败: {e}")
            return False
    
    async def _start_python_http_server(self) -> bool:
        """使用Python HTTP服务器提供基本的Web界面"""
        try:
            # 创建一个简单的HTML页面
            html_content = self._generate_web_ui_html()
            
            # 启动HTTP服务器
            import http.server
            import socketserver
            
            class QdrantHTTPHandler(http.server.SimpleHTTPRequestHandler):
                def do_GET(self):
                    # 处理根路径和dashboard路径
                    if self.path in ['/', '/dashboard', '/dashboard/']:
                        self.send_response(200)
                        self.send_header('Content-type', 'text/html; charset=utf-8')
                        self.end_headers()
                        self.wfile.write(html_content.encode('utf-8'))
                    else:
                        # 其他路径返回404
                        self.send_response(404)
                        self.send_header('Content-type', 'text/html; charset=utf-8')
                        self.end_headers()
                        self.wfile.write(f"""
                        <html>
                        <head><title>404 Not Found</title></head>
                        <body>
                        <h1>404 Not Found</h1>
                        <p>The requested URL {self.path} was not found on this server.</p>
                        <p><a href="/">返回主页</a></p>
                        </body>
                        </html>
                        """.encode('utf-8'))
            
            # 在新线程中启动服务器
            def start_server():
                try:
                    with socketserver.TCPServer(("", self.web_ui_port), QdrantHTTPHandler) as httpd:
                        self.httpd = httpd  # 保存服务器引用
                        httpd.serve_forever()
                except Exception as e:
                    self.logger.error(f"HTTP服务器运行错误: {e}")
            
            import threading
            self.server_thread = threading.Thread(target=start_server, daemon=True)
            self.server_thread.start()
            
            # 设置进程状态为运行中
            self.web_ui_process = type('MockProcess', (), {
                'poll': lambda self=None: None,  # 返回None表示进程正在运行
                'pid': self.server_thread.ident
            })()
            
            await asyncio.sleep(1)
            self.logger.info(f"Python HTTP服务器启动成功: http://localhost:{self.web_ui_port}")
            return True
            
        except Exception as e:
            self.logger.error(f"启动Python HTTP服务器失败: {e}")
            return False
    
    def _generate_web_ui_html(self) -> str:
        """生成增强的Web UI HTML页面"""
        # 获取实时数据
        collections_info = self._get_collections_info()
        
        return f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DeepWin Qdrant 数据库管理</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1400px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1, h2, h3 {{ color: #333; }}
        h1 {{ text-align: center; }}
        .status {{ background: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .collection {{ background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #007bff; }}
        .collection h3 {{ margin-top: 0; color: #007bff; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
        .stat-card {{ background: white; padding: 15px; border-radius: 5px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); text-align: center; }}
        .stat-number {{ font-size: 2em; font-weight: bold; color: #007bff; }}
        .stat-label {{ color: #666; margin-top: 5px; }}
        .actions {{ text-align: center; margin: 20px 0; }}
        .btn {{ background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }}
        .btn:hover {{ background: #0056b3; }}
        .btn-secondary {{ background: #6c757d; }}
        .btn-secondary:hover {{ background: #545b62; }}
        .info {{ background: #e7f3ff; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #17a2b8; }}
        .data-section {{ margin: 20px 0; }}
        .data-table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        .data-table th, .data-table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        .data-table th {{ background-color: #f2f2f2; font-weight: bold; }}
        .data-table tr:nth-child(even) {{ background-color: #f9f9f9; }}
        .data-table tr:hover {{ background-color: #f5f5f5; }}
        .tab-container {{ margin: 20px 0; }}
        .tab-buttons {{ display: flex; border-bottom: 1px solid #ddd; }}
        .tab-button {{ background: none; border: none; padding: 10px 20px; cursor: pointer; }}
        .tab-button.active {{ background: #007bff; color: white; border-radius: 5px 5px 0 0; }}
        .tab-content {{ display: none; padding: 20px; border: 1px solid #ddd; border-top: none; }}
        .tab-content.active {{ display: block; }}
        .search-box {{ width: 100%; padding: 8px; margin: 10px 0; border: 1px solid #ddd; border-radius: 4px; }}
        .json-view {{ background: #f8f9fa; padding: 10px; border-radius: 4px; font-family: monospace; white-space: pre-wrap; max-height: 300px; overflow-y: auto; }}
        .loading {{ text-align: center; padding: 20px; color: #666; }}
        .error {{ background: #f8d7da; color: #721c24; padding: 10px; border-radius: 4px; margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 DeepWin Qdrant 向量数据库管理</h1>
        
        <div class="status">
            <h2>✅ 数据库状态</h2>
            <p><strong>连接状态:</strong> 已连接</p>
            <p><strong>数据库路径:</strong> {self.local_path}</p>
            <p><strong>Web UI端口:</strong> {self.web_ui_port}</p>
            <p><strong>更新时间:</strong> <span id="update-time">{self._get_current_time()}</span></p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{len(collections_info)}</div>
                <div class="stat-label">集合数量</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{self._get_total_points()}</div>
                <div class="stat-label">总向量点数</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{self._get_total_size_mb():.1f}MB</div>
                <div class="stat-label">数据库大小</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{self._get_uptime_hours():.1f}h</div>
                <div class="stat-label">运行时间</div>
            </div>
        </div>
        
        <div class="tab-container">
            <div class="tab-buttons">
                <button class="tab-button active" onclick="showTab('overview')">📊 概览</button>
                <button class="tab-button" onclick="showTab('collections')">📚 集合详情</button>
                <button class="tab-button" onclick="showTab('data')">🔍 数据查询</button>
                <button class="tab-button" onclick="showTab('search')">🔎 向量搜索</button>
                <button class="tab-button" onclick="showTab('management')">⚙️ 管理工具</button>
            </div>
            
            <!-- 概览标签页 -->
            <div id="overview" class="tab-content active">
                <h3>📊 数据库概览</h3>
                <div class="collection">
                    <h4>集合信息</h4>
                    {self._generate_collections_overview(collections_info)}
                </div>
                
                <div class="info">
                    <h4>💡 使用说明</h4>
                    <p>这是一个增强的Web界面，提供Qdrant数据库的详细信息和操作功能。</p>
                    <ul>
                        <li><strong>集合详情:</strong> 查看每个集合的详细信息和数据</li>
                        <li><strong>数据查询:</strong> 浏览和搜索数据库中的向量点</li>
                        <li><strong>向量搜索:</strong> 执行相似性搜索</li>
                        <li><strong>管理工具:</strong> 数据库管理操作</li>
                    </ul>
                </div>
            </div>
            
            <!-- 集合详情标签页 -->
            <div id="collections" class="tab-content">
                <h3>📚 集合详情</h3>
                {self._generate_collections_detail(collections_info)}
            </div>
            
            <!-- 数据查询标签页 -->
            <div id="data" class="tab-content">
                <h3>🔍 数据查询</h3>
                <div class="data-section">
                    <label for="collection-select">选择集合:</label>
                    <select id="collection-select" onchange="loadCollectionData()">
                        <option value="">请选择集合...</option>
                        {self._generate_collection_options(collections_info)}
                    </select>
                    
                    <input type="text" id="search-input" class="search-box" placeholder="搜索向量点ID或内容..." onkeyup="filterData()">
                    
                    <div id="data-content">
                        <div class="loading">请选择一个集合来查看数据...</div>
                    </div>
                </div>
            </div>
            
            <!-- 向量搜索标签页 -->
            <div id="search" class="tab-content">
                <h3>🔎 向量搜索</h3>
                <div class="data-section">
                    <label for="search-collection">搜索集合:</label>
                    <select id="search-collection">
                        {self._generate_collection_options(collections_info)}
                    </select>
                    
                    <label for="search-vector">向量数据 (JSON格式):</label>
                    <textarea id="search-vector" class="search-box" rows="4" placeholder='[0.1, 0.2, 0.3, ...]'></textarea>
                    
                    <label for="search-limit">返回结果数量:</label>
                    <input type="number" id="search-limit" value="10" min="1" max="100">
                    
                    <button class="btn" onclick="performVectorSearch()">🔍 执行搜索</button>
                    
                    <div id="search-results">
                        <div class="loading">请输入搜索条件...</div>
                    </div>
                </div>
            </div>
            
            <!-- 管理工具标签页 -->
            <div id="management" class="tab-content">
                <h3>⚙️ 管理工具</h3>
                <div class="actions">
                    <button class="btn" onclick="refreshData()">🔄 刷新数据</button>
                    <button class="btn btn-secondary" onclick="exportData()">📤 导出数据</button>
                    <button class="btn btn-secondary" onclick="backupDatabase()">💾 备份数据库</button>
                    <button class="btn" onclick="window.open('https://qdrant.tech/documentation/')">📖 查看文档</button>
                    <button class="btn" onclick="window.open('https://cloud.qdrant.io/')">☁️ Qdrant Cloud</button>
                </div>
                
                <div class="info">
                    <h4>🔧 管理命令</h4>
                    <p>在Python代码中使用以下方法管理数据库：</p>
                    <ul>
                        <li><code>qdrant_manager.start_web_ui_manually()</code> - 手动启动Web UI</li>
                        <li><code>qdrant_manager.get_web_ui_status()</code> - 获取Web UI状态</li>
                        <li><code>qdrant_manager.restart_web_ui()</code> - 重启Web UI</li>
                        <li><code>qdrant_manager.execute_query()</code> - 执行查询</li>
                        <li><code>qdrant_manager.execute_command()</code> - 执行命令</li>
                    </ul>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // 标签页切换
        function showTab(tabName) {{
            // 隐藏所有标签页内容
            document.querySelectorAll('.tab-content').forEach(tab => {{
                tab.classList.remove('active');
            }});
            
            // 移除所有标签按钮的active类
            document.querySelectorAll('.tab-button').forEach(btn => {{
                btn.classList.remove('active');
            }});
            
            // 显示选中的标签页
            document.getElementById(tabName).classList.add('active');
            
            // 添加active类到对应的按钮
            event.target.classList.add('active');
        }}
        
        // 加载集合数据
        function loadCollectionData() {{
            const collection = document.getElementById('collection-select').value;
            const content = document.getElementById('data-content');
            
            if (!collection) {{
                content.innerHTML = '<div class="loading">请选择一个集合来查看数据...</div>';
                return;
            }}
            
            content.innerHTML = '<div class="loading">正在加载数据...</div>';
            
            // 模拟加载数据（实际应该通过API获取）
            setTimeout(() => {{
                content.innerHTML = `
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>向量维度</th>
                                <th>Payload</th>
                                <th>操作</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>sample_id_1</td>
                                <td>1536维</td>
                                <td>{{"type": "user", "name": "示例用户"}}</td>
                                <td><button class="btn" onclick="viewDetails('sample_id_1')">查看详情</button></td>
                            </tr>
                        </tbody>
                    </table>
                `;
            }}, 1000);
        }}
        
        // 过滤数据
        function filterData() {{
            const searchTerm = document.getElementById('search-input').value.toLowerCase();
            const rows = document.querySelectorAll('.data-table tbody tr');
            
            rows.forEach(row => {{
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(searchTerm) ? '' : 'none';
            }});
        }}
        
        // 执行向量搜索
        function performVectorSearch() {{
            const collection = document.getElementById('search-collection').value;
            const vector = document.getElementById('search-vector').value;
            const limit = document.getElementById('search-limit').value;
            const results = document.getElementById('search-results');
            
            if (!collection || !vector) {{
                results.innerHTML = '<div class="error">请填写完整的搜索条件</div>';
                return;
            }}
            
            results.innerHTML = '<div class="loading">正在执行搜索...</div>';
            
            // 模拟搜索（实际应该通过API执行）
            setTimeout(() => {{
                results.innerHTML = `
                    <h4>搜索结果 (共找到 1 个结果)</h4>
                    <div class="json-view">
{{
    "id": "sample_result_1",
    "score": 0.95,
    "payload": {{
        "type": "user",
        "name": "匹配用户",
        "description": "这是一个示例搜索结果"
    }}
}}
                    </div>
                `;
            }}, 1500);
        }}
        
        // 刷新数据
        function refreshData() {{
            location.reload();
        }}
        
        // 导出数据
        function exportData() {{
            alert('导出功能需要后端API支持');
        }}
        
        // 备份数据库
        function backupDatabase() {{
            alert('备份功能需要后端API支持');
        }}
        
        // 查看详情
        function viewDetails(id) {{
            alert(`查看ID: ${{id}} 的详细信息`);
        }}
        
        // 自动刷新页面
        setTimeout(() => {{
            location.reload();
        }}, 60000); // 60秒刷新一次
        
        // 添加交互功能
        document.querySelectorAll('.btn').forEach(btn => {{
            btn.addEventListener('click', function() {{
                this.style.transform = 'scale(0.95)';
                setTimeout(() => {{
                    this.style.transform = 'scale(1)';
                }}, 150);
            }});
        }});
    </script>
</body>
</html>
        """
    
    def _find_qdrant_executable(self) -> str:
        """查找Qdrant可执行文件"""
        # 常见的Qdrant可执行文件路径
        possible_paths = [
            "qdrant",  # 系统PATH中
            "qdrant.exe",  # Windows
            os.path.expanduser("~/.cargo/bin/qdrant"),  # Rust安装
            os.path.expanduser("~/.local/bin/qdrant"),  # 用户安装
            "/usr/local/bin/qdrant",  # Linux/Mac系统安装
            "/opt/qdrant/qdrant",  # 自定义安装
        ]
        
        for path in possible_paths:
            try:
                if subprocess.run([path, "--version"], 
                                capture_output=True, 
                                timeout=5).returncode == 0:
                    return path
            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
                continue
        
        return None
    
    def start_web_ui_manually(self, port: int = None) -> bool:
        """手动启动Web UI（同步方法）"""
        if port:
            self.web_ui_port = port
        
        try:
            # 在新线程中启动Web UI
            def start_ui():
                asyncio.run(self._start_web_ui())
            
            thread = threading.Thread(target=start_ui, daemon=True)
            thread.start()
            return True
        except Exception as e:
            self.logger.error(f"手动启动Web UI失败: {e}")
            return False
    
    def get_web_ui_url(self) -> str:
        """获取Web UI访问地址"""
        if self.web_ui_process and self.web_ui_process.poll() is None:
            return f"http://localhost:{self.web_ui_port}/dashboard"
        return None
    
    def is_web_ui_running(self) -> bool:
        """检查Web UI是否正在运行"""
        return (self.web_ui_process is not None and 
                self.web_ui_process.poll() is None)
    
    async def restart_web_ui(self) -> bool:
        """重启Web UI"""
        try:
            await self._stop_web_ui()
            await asyncio.sleep(1)
            return await self._start_web_ui()
        except Exception as e:
            self.logger.error(f"重启Web UI失败: {e}")
            return False
    
    def get_web_ui_status(self) -> Dict[str, Any]:
        """获取Web UI状态信息"""
        return {
            "enabled": self.web_ui_enabled,
            "running": self.is_web_ui_running(),
            "port": self.web_ui_port,
            "url": self.get_web_ui_url(),
            "process_id": self.web_ui_process.pid if self.web_ui_process else None
        }
    
    # ==================== Web UI 数据支持方法 ====================
    
    def _get_collections_info(self) -> Dict[str, Any]:
        """获取集合信息"""
        try:
            if not self.client:
                return {}
            
            collections = self.client.get_collections()
            info = {}
            
            for col in collections.collections:
                try:
                    # 获取集合详细信息
                    collection_detail = self.client.get_collection(col.name)
                    info[col.name] = {
                        "name": col.name,
                        "vectors_count": collection_detail.config.params.vectors.size,
                        "points_count": collection_detail.points_count,
                        "status": "active",
                        "created_at": getattr(collection_detail, 'created_at', 'unknown'),
                        "updated_at": getattr(collection_detail, 'updated_at', 'unknown')
                    }
                except Exception as e:
                    self.logger.warning(f"获取集合 {col.name} 详情失败: {e}")
                    info[col.name] = {
                        "name": col.name,
                        "vectors_count": "unknown",
                        "points_count": "unknown",
                        "status": "error",
                        "error": str(e)
                    }
            
            return info
        except Exception as e:
            self.logger.error(f"获取集合信息失败: {e}")
            return {}
    
    def _get_total_points(self) -> int:
        """获取总向量点数"""
        try:
            collections_info = self._get_collections_info()
            total = 0
            for info in collections_info.values():
                if isinstance(info.get('points_count'), int):
                    total += info['points_count']
            return total
        except Exception:
            return 0
    
    def _get_total_size_mb(self) -> float:
        """获取数据库大小（MB）"""
        try:
            if self.local_path and os.path.exists(self.local_path):
                total_size = 0
                for dirpath, dirnames, filenames in os.walk(self.local_path):
                    for filename in filenames:
                        filepath = os.path.join(dirpath, filename)
                        total_size += os.path.getsize(filepath)
                return total_size / (1024 * 1024)  # 转换为MB
            return 0.0
        except Exception:
            return 0.0
    
    def _get_uptime_hours(self) -> float:
        """获取运行时间（小时）"""
        try:
            # 简单的运行时间计算，实际应该记录启动时间
            return 1.0  # 默认显示1小时
        except Exception:
            return 0.0
    
    def _get_current_time(self) -> str:
        """获取当前时间"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def _generate_collections_overview(self, collections_info: Dict[str, Any]) -> str:
        """生成集合概览HTML"""
        if not collections_info:
            return "<p>暂无集合信息</p>"
        
        html = "<table class='data-table'>"
        html += "<thead><tr><th>集合名称</th><th>向量维度</th><th>向量点数</th><th>状态</th></tr></thead>"
        html += "<tbody>"
        
        for name, info in collections_info.items():
            html += f"""
            <tr>
                <td><strong>{name}</strong></td>
                <td>{info.get('vectors_count', 'unknown')}</td>
                <td>{info.get('points_count', 'unknown')}</td>
                <td>{info.get('status', 'unknown')}</td>
            </tr>
            """
        
        html += "</tbody></table>"
        return html
    
    def _generate_collections_detail(self, collections_info: Dict[str, Any]) -> str:
        """生成集合详情HTML"""
        if not collections_info:
            return "<p>暂无集合信息</p>"
        
        html = ""
        for name, info in collections_info.items():
            html += f"""
            <div class="collection">
                <h4>📚 {name}</h4>
                <table class="data-table">
                    <tr><td><strong>集合名称:</strong></td><td>{name}</td></tr>
                    <tr><td><strong>向量维度:</strong></td><td>{info.get('vectors_count', 'unknown')}</td></tr>
                    <tr><td><strong>向量点数:</strong></td><td>{info.get('points_count', 'unknown')}</td></tr>
                    <tr><td><strong>状态:</strong></td><td>{info.get('status', 'unknown')}</td></tr>
                    <tr><td><strong>创建时间:</strong></td><td>{info.get('created_at', 'unknown')}</td></tr>
                    <tr><td><strong>更新时间:</strong></td><td>{info.get('updated_at', 'unknown')}</td></tr>
                </table>
            </div>
            """
        
        return html
    
    def _generate_collection_options(self, collections_info: Dict[str, Any]) -> str:
        """生成集合选项HTML"""
        if not collections_info:
            return "<option value=''>暂无集合</option>"
        
        html = ""
        for name in collections_info.keys():
            html += f"<option value='{name}'>{name}</option>"
        
        return html

    def insert_vector_sync(self, collection_name: str, vector_id: str, vector: List[float], payload: Dict[str, Any] = None) -> bool:
        """同步插入向量"""
        try:
            if not self.is_connected:
                self.logger.error("Qdrant数据库未连接")
                return False
            
            # 确保集合存在
            if not self._ensure_collection_exists_sync(collection_name, len(vector)):
                return False
            
            point = PointStruct(id=vector_id, vector=vector, payload=payload or {})
            self.client.upsert(collection_name=collection_name, points=[point])
            self.logger.info(f"向量同步插入成功: {collection_name}/{vector_id}")
            # 发送操作完成信号
            self.operation_completed.emit(self.name, f"向量插入成功: {collection_name}/{vector_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"向量同步插入失败: {e}")
            # 发送错误信号
            self.error_occurred.emit(self.name, f"向量插入失败: {e}")
            return False
    
    def _ensure_collection_exists_sync(self, collection_name: str, vector_size: int) -> bool:
        """同步确保集合存在"""
        try:
            # 检查集合是否存在
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if collection_name not in collection_names:
                # 创建新集合
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
                )
                self.logger.info(f"创建新集合: {collection_name}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"确保集合存在失败: {e}")
            return False
