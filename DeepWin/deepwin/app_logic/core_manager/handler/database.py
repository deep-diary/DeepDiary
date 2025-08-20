# src/app_logic/core_manager/handler/database_handler.py
# 数据库处理器，负责处理所有数据库相关的信号连接和事件处理

import asyncio
import concurrent.futures
from datetime import datetime
from typing import Dict, Any, Optional
from PySide6.QtCore import Slot, QTimer

from deepwin.app_logic.core_manager.base_handler import BaseHandler


class DatabaseHandler(BaseHandler):
    """
    数据库处理器
    负责处理数据库信号和执行业务逻辑（如创建示例数据）
    数据库实例通过BaseHandler基类获取，初始化由LocalDatabaseManager负责
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 示例数据创建状态
        self.sample_data_creation_status = {
            'sqlite': {'status': 'pending', 'message': '等待初始化'},
            'qdrant': {'status': 'pending', 'message': '等待初始化'}
        }
        
        # 示例数据创建标志，避免重复创建
        self.sample_data_created = False
        
    def _validate_dependencies(self):
        """
        验证必需的依赖项是否已设置
        """
        # 检查基础依赖项
        if not self.logger:
            raise ValueError("缺少必需的依赖项: logger")
        if not self.local_database_manager:
            raise ValueError("缺少必需的依赖项: local_database_manager")
        if not self.coordinator_handler:
            raise ValueError("缺少必需的依赖项: coordinator_handler")
        if not self.sqlite_db:
            raise ValueError("缺少必需的依赖项: sqlite_db")
        if not self.qdrant_db:
            raise ValueError("缺少必需的依赖项: qdrant_db")

    def _connect_signals(self):
        """
        连接数据库相关的信号
        """
        self.logger.debug("DatabaseHandler: 连接数据库相关信号...")
        
        # 连接本地数据库管理器的统一信号出口
        if self.local_database_manager:
            # 基础信号
            self.local_database_manager.database_ready.connect(self._on_database_ready)
            self.local_database_manager.data_operation_completed.connect(self._on_data_operation_completed)
            self.local_database_manager.connection_status_changed.connect(self._on_connection_status_changed)
            self.local_database_manager.error_occurred.connect(self._on_error_occurred)
            
            self.logger.info("DatabaseHandler: 已连接本地数据库管理器的所有信号")
        
        self.logger.debug("DatabaseHandler: 数据库相关信号连接完成")
        
    def _create_sample_data_after_delay(self):
        """
        延迟创建示例数据，确保数据库完全就绪
        注意：虽然收到database_ready信号，但可能还需要等待内部状态同步
        """
        if self.sample_data_created:
            self.logger.info("DatabaseHandler: 示例数据已创建，跳过")
            return
            
        # 检查数据库连接状态，如果已连接则直接创建，否则延迟执行
        if (self.sqlite_db and self.sqlite_db.is_connected and 
            self.qdrant_db and self.qdrant_db.is_connected):
            self.logger.info("DatabaseHandler: 数据库已连接，直接创建示例数据")
            self._create_sample_data()
        else:
            self.logger.info("DatabaseHandler: 数据库连接状态检查失败，延迟1秒后重试")
            # 使用定时器延迟执行，给数据库一些初始化时间
            QTimer.singleShot(1000, self._create_sample_data)
    
    def _create_sample_data(self):
        """
        创建示例数据
        """
        if self.sample_data_created:
            self.logger.info("DatabaseHandler: 示例数据已创建，跳过")
            return
            
        self.logger.info("DatabaseHandler: 开始创建示例数据...")
        
        # 创建SQLite示例数据
        if self.sqlite_db and self.sqlite_db.is_connected:
            self._create_sqlite_sample_data()
        else:
            self.logger.warning("DatabaseHandler: SQLite数据库未连接，跳过示例数据创建")
            self.sample_data_creation_status['sqlite']['status'] = 'skipped'
            self.sample_data_creation_status['sqlite']['message'] = '数据库未连接'
        
        # 创建Qdrant示例数据
        if self.qdrant_db and self.qdrant_db.is_connected:
            self._create_qdrant_sample_data()
        else:
            self.logger.warning("DatabaseHandler: Qdrant数据库未连接，跳过示例数据创建")
            self.sample_data_creation_status['qdrant']['status'] = 'skipped'
            self.sample_data_creation_status['qdrant']['message'] = '数据库未连接'
        
        # 标记示例数据已创建
        self.sample_data_created = True
    
    def _create_sqlite_sample_data(self):
        """
        创建SQLite示例数据
        """
        self.logger.info("DatabaseHandler: 开始创建SQLite示例数据...")
        self.sample_data_creation_status['sqlite']['status'] = 'creating'
        self.sample_data_creation_status['sqlite']['message'] = '正在创建示例数据...'
        
        try:
            # 导入模型
            from deepwin.data_management.database.models import (
                get_user_model, get_need_model, get_resource_model, get_photo_model
            )
            
            UserModel = get_user_model()
            NeedModel = get_need_model()
            ResourceModel = get_resource_model()
            PhotoModel = get_photo_model()
            
            # 创建示例用户数据（用户名和邮箱前缀为随机字符串）
            import random
            import string

            def random_str(length=8):
                return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

            sample_users = []
            user_infos = [
                {
                    'phone': '+86-138-0013-8000',
                    'country': 'CN',
                    'city': '深圳',
                    'company': 'DeepWin科技',
                    'industry': '人工智能',
                    'position': '系统管理员'
                },
                {
                    'phone': '+86-139-0013-9000',
                    'country': 'CN',
                    'city': '北京',
                    'company': 'DeepWin科技',
                    'industry': '软件开发',
                    'position': '高级工程师'
                },
                {
                    'phone': '+86-137-0013-7000',
                    'country': 'CN',
                    'city': '上海',
                    'company': 'DeepWin科技',
                    'industry': '质量保证',
                    'position': '测试工程师'
                }
            ]
            for info in user_infos:
                rand_prefix = random_str(10)
                sample_users.append({
                    'username': rand_prefix,
                    'email': f"{rand_prefix}@deepwin.com",
                    **info
                })
            
            # 创建示例需求数据
            sample_needs = [
                {
                    'user_id': 1,  # admin用户
                    'title': '完善数据库架构',
                    'description': '需要优化数据库性能，支持更多并发连接',
                    'category': '系统优化',
                    'priority': 3,  # 高优先级
                    'status': 'active',
                    'tags': '数据库,性能,优化'
                },
                {
                    'user_id': 2,  # developer用户
                    'title': '开发新功能模块',
                    'description': '实现用户管理界面的新功能',
                    'category': '功能开发',
                    'priority': 2,  # 中优先级
                    'status': 'active',
                    'tags': '前端,用户管理,新功能'
                },
                {
                    'user_id': 3,  # tester用户
                    'title': '自动化测试脚本',
                    'description': '编写完整的自动化测试用例',
                    'category': '测试',
                    'priority': 2,  # 中优先级
                    'status': 'on_hold',
                    'tags': '测试,自动化,脚本'
                }
            ]
            
            # 创建示例资源数据
            sample_resources = [
                {
                    'user_id': 1,
                    'title': '数据库设计文档',
                    'resource_type': 'material',
                    'category': 'document',
                    'description': '数据库架构设计文档，包含表结构和关系设计',
                    'status': 'available',
                    'tags': '文档,数据库,设计'
                },
                {
                    'user_id': 2,
                    'title': '源代码仓库',
                    'resource_type': 'network',
                    'category': 'repository',
                    'description': 'GitHub源代码仓库，包含项目所有代码',
                    'status': 'available',
                    'tags': '代码,仓库,Git'
                },
                {
                    'user_id': 3,
                    'title': '测试报告模板',
                    'resource_type': 'material',
                    'category': 'template',
                    'description': '标准测试报告模板，用于记录测试结果',
                    'status': 'available',
                    'tags': '模板,测试,报告'
                }
            ]
            
            # 创建示例照片数据
            sample_photos = [
                {
                    'user_id': 1,
                    'file_path': '/photos/team_photo.jpg',
                    'file_name': 'team_photo.jpg',
                    'file_size': 3145728,  # 3MB
                    'mime_type': 'image/jpeg',
                    'description': '团队合影照片',
                    'tags': '团队,合影,工作照',
                    'location': '深圳',
                    'taken_at': datetime.now().replace(hour=9, minute=0)
                },
                {
                    'user_id': 2,
                    'file_path': '/photos/office_view.jpg',
                    'file_name': 'office_view.jpg',
                    'file_size': 2097152,  # 2MB
                    'mime_type': 'image/jpeg',
                    'description': '办公室环境照片',
                    'tags': '办公室,环境,工作',
                    'location': '北京',
                    'taken_at': datetime.now().replace(hour=11, minute=30)
                }
            ]
            
            # 同步插入数据（避免事件循环问题）
            try:
                # 插入用户数据
                for user_data in sample_users:
                    user = UserModel(**user_data)
                    success = self.sqlite_db.insert_model_sync(user)
                    if not success:
                        self.logger.error(f"用户数据插入失败: {user_data['username']}")
                
                # 插入需求数据
                for need_data in sample_needs:
                    need = NeedModel(**need_data)
                    success = self.sqlite_db.insert_model_sync(need)
                    if not success:
                        self.logger.error(f"需求数据插入失败: {need_data['title']}")
                
                # 插入资源数据
                for resource_data in sample_resources:
                    resource = ResourceModel(**resource_data)
                    success = self.sqlite_db.insert_model_sync(resource)
                    if not success:
                        self.logger.error(f"资源数据插入失败: {resource_data['title']}")
                
                # 插入照片数据
                for photo_data in sample_photos:
                    photo = PhotoModel(**photo_data)
                    success = self.sqlite_db.insert_model_sync(photo)
                    if not success:
                        self.logger.error(f"照片数据插入失败: {photo_data['file_name']}")
                
                self.logger.info("DatabaseHandler: SQLite示例数据插入完成")
                self.sample_data_creation_status['sqlite']['status'] = 'success'
                self.sample_data_creation_status['sqlite']['message'] = '示例数据创建成功'
                
            except Exception as e:
                self.logger.error(f"DatabaseHandler: SQLite示例数据插入异常: {e}")
                self.sample_data_creation_status['sqlite']['status'] = 'failed'
                self.sample_data_creation_status['sqlite']['message'] = f'异常: {str(e)}'
                
        except Exception as e:
            self.logger.error(f"DatabaseHandler: 创建SQLite示例数据失败: {e}")
            self.sample_data_creation_status['sqlite']['status'] = 'failed'
            self.sample_data_creation_status['sqlite']['message'] = f'创建失败: {str(e)}'
    
    def _create_qdrant_sample_data(self):
        """
        创建Qdrant示例数据
        """
        self.logger.info("DatabaseHandler: 开始创建Qdrant示例数据...")
        self.sample_data_creation_status['qdrant']['status'] = 'creating'
        self.sample_data_creation_status['qdrant']['message'] = '正在创建示例数据...'
        
        try:
            # 示例向量数据
            sample_embeddings = {
                'user_embeddings': [
                    {
                        'id': '550e8400-e29b-41d4-a716-446655440001',
                        'vector': [0.1] * 1536,  # 1536维向量
                        'payload': {
                            'username': 'admin_test',
                            'email': 'admin_test@deepwin.com',
                            'role': 'administrator',
                            'department': 'IT'
                        }
                    },
                    {
                        'id': '550e8400-e29b-41d4-a716-446655440002',
                        'vector': [0.2] * 1536,
                        'payload': {
                            'username': 'developer_test',
                            'email': 'developer_test@deepwin.com',
                            'role': 'developer',
                            'department': 'Engineering'
                        }
                    },
                    {
                        'id': '550e8400-e29b-41d4-a716-446655440003',
                        'vector': [0.3] * 1536,
                        'payload': {
                            'username': 'tester_test',
                            'email': 'tester_test@deepwin.com',
                            'role': 'tester',
                            'department': 'QA'
                        }
                    }
                ],
                'memory_embeddings': [
                    {
                        'id': '550e8400-e29b-41d4-a716-446655440004',
                        'vector': [0.4] * 1536,
                        'payload': {
                            'content': '用户登录系统',
                            'timestamp': '2024-01-15T10:30:00Z',
                            'user_id': '550e8400-e29b-41d4-a716-446655440001',
                            'type': 'login'
                        }
                    },
                    {
                        'id': '550e8400-e29b-41d4-a716-446655440005',
                        'vector': [0.5] * 1536,
                        'payload': {
                            'content': '创建新项目',
                            'timestamp': '2024-01-15T14:20:00Z',
                            'user_id': '550e8400-e29b-41d4-a716-446655440002',
                            'type': 'project_creation'
                        }
                    },
                    {
                        'id': '550e8400-e29b-41d4-a716-446655440006',
                        'vector': [0.6] * 1536,
                        'payload': {
                            'content': '运行测试用例',
                            'timestamp': '2024-01-15T16:45:00Z',
                            'user_id': '550e8400-e29b-41d4-a716-446655440003',
                            'type': 'test_execution'
                        }
                    }
                ],
                'photo_embeddings': [
                    {
                        'id': '550e8400-e29b-41d4-a716-446655440007',
                        'vector': [0.7] * 512,  # 512维向量
                        'payload': {
                            'filename': 'team_photo.jpg',
                            'description': '团队合影照片',
                            'tags': ['团队', '合影', '工作照'],
                            'user_id': '550e8400-e29b-41d4-a716-446655440001',
                            'upload_time': '2024-01-15T09:00:00Z'
                        }
                    },
                    {
                        'id': '550e8400-e29b-41d4-a716-446655440008',
                        'vector': [0.8] * 512,
                        'payload': {
                            'filename': 'office_view.jpg',
                            'description': '办公室环境照片',
                            'tags': ['办公室', '环境', '工作'],
                            'user_id': '550e8400-e29b-41d4-a716-446655440002',
                            'upload_time': '2024-01-15T11:30:00Z'
                        }
                    }
                ]
            }
            
            # 同步插入数据（避免事件循环问题）
            try:
                # 插入用户嵌入向量
                for embedding in sample_embeddings['user_embeddings']:
                    success = self.qdrant_db.insert_vector_sync(
                        collection_name='user_embeddings',
                        vector_id=embedding['id'],
                        vector=embedding['vector'],
                        payload=embedding['payload']
                    )
                    if not success:
                        self.logger.error(f"用户嵌入向量插入失败: {embedding['id']}")
                
                # 插入记忆嵌入向量
                for embedding in sample_embeddings['memory_embeddings']:
                    success = self.qdrant_db.insert_vector_sync(
                        collection_name='memory_embeddings',
                        vector_id=embedding['id'],
                        vector=embedding['vector'],
                        payload=embedding['payload']
                    )
                    if not success:
                        self.logger.error(f"记忆嵌入向量插入失败: {embedding['id']}")
                
                # 插入照片嵌入向量
                for embedding in sample_embeddings['photo_embeddings']:
                    success = self.qdrant_db.insert_vector_sync(
                        collection_name='photo_embeddings',
                        vector_id=embedding['id'],
                        vector=embedding['vector'],
                        payload=embedding['payload']
                    )
                    if not success:
                        self.logger.error(f"照片嵌入向量插入失败: {embedding['id']}")
                
                self.logger.info("DatabaseHandler: Qdrant示例数据插入完成")
                self.sample_data_creation_status['qdrant']['status'] = 'success'
                self.sample_data_creation_status['qdrant']['message'] = '示例数据创建成功'
                
            except Exception as e:
                self.logger.error(f"DatabaseHandler: Qdrant示例数据插入异常: {e}")
                self.sample_data_creation_status['qdrant']['status'] = 'failed'
                self.sample_data_creation_status['qdrant']['message'] = f'异常: {str(e)}'
                
        except Exception as e:
            self.logger.error(f"DatabaseHandler: 创建Qdrant示例数据失败: {e}")
            self.sample_data_creation_status['qdrant']['status'] = 'failed'
            self.sample_data_creation_status['qdrant']['message'] = f'创建失败: {str(e)}'
    

    
    # ==================== 信号处理方法 ====================
    
    @Slot()
    def _on_database_ready(self):
        """
        处理数据库准备就绪信号
        """
        self.logger.info("DatabaseHandler: 收到数据库准备就绪信号")
        
        # 开始创建示例数据
        self._create_sample_data_after_delay()
    
    @Slot(str, str)
    def _on_data_operation_completed(self, operation: str, result: str):
        """
        处理数据操作完成信号（增删改查、同步等）
        """
        self.logger.info(f"DatabaseHandler: 数据库数据操作完成: {operation} - {result}")
        
        # 更新状态消息
        if self.coordinator_handler:
            self.coordinator_handler.app_status_message.emit(f"数据库数据操作完成: {operation}")
    
    @Slot(str, str)
    def _on_error_occurred(self, operation: str, error: str):
        """
        处理错误发生信号
        """
        self.logger.error(f"DatabaseHandler: 数据库操作错误: {operation} - {error}")
        
        # 更新状态消息
        if self.coordinator_handler:
            self.coordinator_handler.app_status_message.emit(f"数据库错误: {operation} - {error}")
    
    @Slot(str, str)
    def _on_connection_status_changed(self, operation: str, result: str):
        """
        处理数据库连接状态变化信号（连接、断开、重连等）
        """
        self.logger.info(f"DatabaseHandler: 收到数据库连接状态变化信号: {operation} - {result}")
        
        # 根据操作类型进行特殊处理
        if operation == "databases_connected":
            self.logger.info(f"DatabaseHandler: 数据库连接成功: {result}")
        elif operation == "databases_disconnected":
            self.logger.info(f"DatabaseHandler: 数据库断开连接: {result}")
        elif operation == "cross_database":
            self.logger.info(f"DatabaseHandler: 跨数据库操作完成: {result}")
        
        # 更新状态消息
        if self.coordinator_handler:
            self.coordinator_handler.app_status_message.emit(f"数据库连接状态变化: {operation}")
    
    # ==================== 公共方法 ====================
    
    def cleanup(self):
        """
        清理资源
        """
        self.logger.info("DatabaseHandler: 执行清理工作...")
        
        # 示例数据创建标志已移除，不再需要清理
        
        self.logger.info("DatabaseHandler: 清理完成")
