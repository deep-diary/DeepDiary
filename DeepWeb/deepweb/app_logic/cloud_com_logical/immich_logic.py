"""
Immich 业务逻辑层

这个模块提供基于 ImmichAPI 的业务逻辑功能，组合多个 API 调用来实现复杂的业务场景。
例如：搜索资产并下载缩略图、批量处理资产等。

架构说明：
- immich_api.py: API 层，封装单个 API 调用
- immich_logic.py: 业务逻辑层，组合多个 API 调用实现业务功能
"""

from typing import Optional, Dict, List, Union
from pathlib import Path
import asyncio
import time
from datetime import datetime

from immich_python_sdk.models.asset_media_size import AssetMediaSize
from deepweb.services.cloud_communication.immich_api import ImmichAPI, _detect_image_format
import logging

logger = logging.getLogger(__name__)


class ImmichLogic:
    """
    Immich 业务逻辑处理类
    
    提供高级业务功能，组合多个 API 调用来实现复杂的业务场景。
    """
    
    def __init__(self, immich_api: ImmichAPI):
        """
        初始化业务逻辑处理器
        
        Args:
            immich_api: ImmichAPI 实例，用于调用底层 API
        """
        self.api = immich_api
        if not self.api.enabled:
            logger.warning("Immich API未启用，业务逻辑功能将被禁用")
    
    async def search_random_by_person(
        self,
        person_name: str,
        size: int = 4,
        city: Optional[str] = None,
        date: Optional[tuple] = None,
        **kwargs
    ) -> Optional[List[Dict]]:
        """
        根据人物姓名和数量进行随机搜索，返回资产列表
        
        业务场景：用户提供人物名称，随机获取该人物的一些照片，用于前端展示
        
        Args:
            person_name: 人物名称
            size: 返回的资产数量，默认10
            city: 城市名称（可选）
            date: 日期范围元组 (taken_after, taken_before)，可选
            **kwargs: 其他搜索参数（传递给 search_random）
        
        Returns:
            资产列表（字典格式），如果搜索失败返回None
        """
        if not self.api.enabled:
            logger.warning("Immich API未启用，无法执行随机搜索")
            return None
        
        try:
            # 先搜索人物ID
            person_ids = await self.api.search_person(name=person_name, return_ids=True, timeout=5.0)
            
            if not person_ids:
                logger.warning(f"[immich_logic] 未找到名为 '{person_name}' 的人物")
                return None
            
            logger.info(f"[immich_logic] 找到人物ID: {person_ids}，开始随机搜索资产")
            
            # 使用人物ID进行随机搜索
            search_kwargs = {
                "person_ids": person_ids,
                "size": size,
            }
            
            # 处理城市参数
            if city:
                search_kwargs["city"] = city
            
            # 处理日期范围
            if date:
                taken_after, taken_before = date
                if taken_after:
                    search_kwargs["taken_after"] = taken_after
                if taken_before:
                    search_kwargs["taken_before"] = taken_before
            
            # 添加其他参数
            search_kwargs.update(kwargs)
            
            assets = await self.api.search_random(**search_kwargs)
            
            # 确保返回的是列表类型
            if assets is not None:
                if not isinstance(assets, list):
                    logger.error(f"[immich_logic] search_random 返回了非列表类型: {type(assets)}, 值: {assets}")
                    return None
                if len(assets) > 0:
                    logger.info(f"[immich_logic] 随机搜索完成: 找到 {len(assets)} 个资产")
                    return assets
                else:
                    logger.warning(f"[immich_logic] 随机搜索未找到资产")
                    return None
            else:
                logger.warning(f"[immich_logic] 随机搜索返回 None")
                return None
                
        except Exception as e:
            logger.error(f"[immich_logic] 随机搜索异常: {e}", exc_info=True)
            return None
    
    async def search_smart_assets(
        self,
        query: str = "",
        person_name: Optional[str] = None,
        city: Optional[str] = None,
        date: Optional[tuple] = None,
        size: Optional[int] = None,
        **kwargs
    ) -> Optional[List[Dict]]:
        """
        根据时间、地点、人物、描述、数量进行智能检索，返回资产列表
        
        业务场景：根据多个条件智能搜索资产，返回资产列表供前端展示
        
        Args:
            query: 搜索查询字符串（描述）
            person_name: 人物名称（可选）
            city: 城市名称（可选）
            date: 日期范围元组 (taken_after, taken_before)，可选
            size: 每页数量，默认None（使用服务器默认值）
            **kwargs: 其他搜索参数（传递给 search_smart）
        
        Returns:
            资产列表（字典格式），如果搜索失败返回None
        """
        if not self.api.enabled:
            logger.warning("Immich API未启用，无法执行智能搜索")
            return None
        
        try:
            # 准备搜索参数
            search_kwargs = {}
            
            # 处理人物名称
            if person_name:
                person_ids = await self.api.search_person(name=person_name, return_ids=True, timeout=5.0)
                if person_ids:
                    search_kwargs["person_ids"] = person_ids
                    logger.info(f"[immich_logic] 使用人物ID进行搜索: {person_ids}")
                else:
                    # 如果未找到人物ID，将人物名称添加到查询字符串中
                    if query:
                        query = f"{query} {person_name}"
                    else:
                        query = person_name
            
            # 处理城市
            if city:
                search_kwargs["city"] = city
            
            # 处理日期范围
            if date:
                taken_after, taken_before = date
                if taken_after:
                    search_kwargs["taken_after"] = taken_after
                if taken_before:
                    search_kwargs["taken_before"] = taken_before
            
            # 如果没有查询字符串，使用默认值
            if not query:
                query = "photo"
            
            # 添加其他参数
            search_kwargs.update(kwargs)
            
            logger.info(
                f"[immich_logic] 开始智能搜索: query='{query}', "
                f"size={size}, search_kwargs={search_kwargs}"
            )
            
            # 执行智能搜索
            search_result = await self.api.search_smart(query=query, size=size, **search_kwargs)
            
            if not search_result:
                logger.warning("[immich_logic] 智能搜索未返回结果")
                return None
            
            # 提取资产列表
            assets_data = search_result.get('assets', {})
            assets_items = assets_data.get('items', [])
            
            # 确保返回的是列表类型
            if assets_items:
                if not isinstance(assets_items, list):
                    logger.error(f"[immich_logic] search_smart 返回的 items 不是列表类型: {type(assets_items)}, 值: {assets_items}")
                    return None
                logger.info(f"[immich_logic] 智能搜索完成: 找到 {len(assets_items)} 个资产")
                return assets_items
            else:
                logger.warning("[immich_logic] 智能搜索未找到资产")
                return None
                
        except Exception as e:
            logger.error(f"[immich_logic] 智能搜索异常: {e}", exc_info=True)
            return None
    
    async def search_and_download_thumbnails(
        self,
        query: str,
        save_dir: Union[str, Path],
        thumbnail_size: AssetMediaSize = AssetMediaSize.THUMBNAIL,
        max_count: Optional[int] = None,
        person_name: Optional[str] = None,
        **search_kwargs
    ) -> Dict[str, any]:
        """
        搜索资产并下载缩略图到本地
        
        业务场景：根据搜索条件查找相关资产，然后将缩略图下载到本地用于web显示
        
        Args:
            query: 搜索查询字符串
            save_dir: 保存目录路径（str 或 Path）
            thumbnail_size: 缩略图尺寸，默认 THUMBNAIL
            max_count: 最大下载数量，None 表示下载所有结果
            person_name: 人物名称（可选），如果提供会先搜索人物ID，然后添加到搜索参数中
            **search_kwargs: 其他搜索参数（传递给 search_smart）
        
        Returns:
            包含以下字段的字典:
            - success: 是否成功
            - total_found: 找到的资产总数
            - downloaded: 成功下载的数量
            - failed: 下载失败的数量
            - saved_files: 保存的文件路径列表
            - errors: 错误信息列表
        """
        if not self.api.enabled:
            logger.warning("Immich API未启用，无法执行搜索和下载")
            return {
                "success": False,
                "total_found": 0,
                "downloaded": 0,
                "failed": 0,
                "saved_files": [],
                "errors": ["Immich API未启用"]
            }
        
        # 确保保存目录存在
        save_path = Path(save_dir)
        save_path.mkdir(parents=True, exist_ok=True)
        
        result = {
            "success": False,
            "total_found": 0,
            "downloaded": 0,
            "failed": 0,
            "saved_files": [],
            "errors": []
        }
        
        try:
            # 步骤0: 如果提供了人物名称，先搜索人物ID
            if person_name:
                # 调用API层的方法获取人物ID
                person_ids = await self.api.search_person(name=person_name, return_ids=True, timeout=5.0)
                if person_ids:
                    # 将人物ID添加到搜索参数中
                    search_kwargs["person_ids"] = person_ids
                    logger.info(f"[immich_logic] 使用人物ID进行搜索: {person_ids}")
                else:
                    # 如果未找到人物ID，将人物名称添加到查询字符串中
                    logger.warning(f"[immich_logic] 未找到人物ID，将人物名称添加到查询字符串")
                    if query:
                        query = f"{query} {person_name}"
                    else:
                        query = person_name
            
            # 步骤1: 执行搜索
            logger.info(
                f"[immich_logic] 开始搜索资产: query='{query}', "
                f"max_count={max_count}, search_kwargs={search_kwargs}"
            )
            logger.info(f"[immich_logic] 调用 api.search_smart 开始...")
            search_start_time = time.time()
            search_result = await self.api.search_smart(query=query, **search_kwargs)
            search_duration = time.time() - search_start_time
            logger.info(f"[immich_logic] api.search_smart 完成，耗时: {search_duration:.2f}秒")
            
            if not search_result:
                logger.warning("[immich_logic] 搜索未返回结果")
                result["errors"].append("搜索未返回结果")
                return result
            
            # 提取资产列表
            assets_data = search_result.get('assets', {})
            assets_items = assets_data.get('items', [])
            total_found = assets_data.get('total', 0)
            
            result["total_found"] = total_found
            
            if not assets_items:
                logger.info("搜索未找到任何资产")
                result["success"] = True  # 搜索成功，只是没有结果
                return result
            
            # 限制下载数量
            if max_count:
                assets_items = assets_items[:max_count]
            
            logger.info(f"[immich_logic] 找到 {len(assets_items)} 个资产，准备下载缩略图...")
            
            # 步骤2: 批量下载缩略图
            download_tasks = []
            for idx, asset in enumerate(assets_items):
                asset_id = asset.get('id')
                if asset_id:
                    logger.debug(f"[immich_logic] 准备下载第 {idx+1}/{len(assets_items)} 个资产: {asset_id}")
                    download_tasks.append(
                        self._download_single_thumbnail(
                            asset_id=asset_id,
                            asset_info=asset,
                            save_dir=save_path,
                            thumbnail_size=thumbnail_size
                        )
                    )
            
            logger.info(f"[immich_logic] 开始并发下载 {len(download_tasks)} 个缩略图...")
            download_start_time = time.time()
            # 并发执行下载任务
            download_results = await asyncio.gather(*download_tasks, return_exceptions=True)
            download_duration = time.time() - download_start_time
            logger.info(f"[immich_logic] 并发下载完成，耗时: {download_duration:.2f}秒")
            
            # 统计结果
            for download_result in download_results:
                if isinstance(download_result, Exception):
                    result["failed"] += 1
                    result["errors"].append(str(download_result))
                    logger.error(f"下载缩略图异常: {download_result}")
                elif download_result and download_result.get("success"):
                    result["downloaded"] += 1
                    result["saved_files"].append(download_result.get("file_path"))
                else:
                    result["failed"] += 1
                    if download_result:
                        result["errors"].append(download_result.get("error", "未知错误"))
            
            result["success"] = result["downloaded"] > 0
            
            logger.info(
                f"下载完成: 成功 {result['downloaded']} 个, "
                f"失败 {result['failed']} 个, "
                f"总计 {result['total_found']} 个"
            )
            
        except Exception as e:
            logger.error(f"搜索和下载缩略图异常: {e}", exc_info=True)
            result["errors"].append(f"异常: {str(e)}")
        
        return result
    
    async def _download_single_thumbnail(
        self,
        asset_id: str,
        asset_info: Optional[Dict],
        save_dir: Optional[Path],
        thumbnail_size: AssetMediaSize,
        return_base64: bool = True,
        return_pil: bool = False
    ) -> Dict[str, any]:
        """
        下载单个资产的缩略图（内部辅助方法）
        
        Args:
            asset_id: 资产ID
            asset_info: 资产信息字典（可选，用于获取文件名等信息）
            save_dir: 保存目录（可选，如果 return_base64=True 或 return_pil=True 则不需要）
            thumbnail_size: 缩略图尺寸
            return_base64: 是否返回 base64 data URI（True）或文件路径（False）
            return_pil: 是否返回 PIL Image 对象（优先级高于 return_base64）
        
        Returns:
            包含 success、file_path/base64_data_uri/pil_image、error 的字典
        
        性能对比：
        - PIL Image 对象：内存占用最小，无需编码/解码，Gradio 直接使用，性能最优
        - base64 data URI：内存占用增加约 33%，需要编码，Gradio 需要解析，性能中等
        - 文件路径：需要文件 I/O，性能最差
        """
        import time
        import base64
        task_start_time = time.time()
        
        try:
            # 使用 view_asset_with_info 获取图片数据和 Content-Type
            api_start_time = time.time()
            response_info = await self.api.view_asset_with_info(
                asset_id=asset_id,
                size=thumbnail_size
            )
            api_end_time = time.time()
            api_duration = (api_end_time - api_start_time) * 1000
            
            if not response_info or not response_info.get('data'):
                logger.warning(f"[性能] {asset_id} API 调用耗时: {api_duration:.2f}ms, 但返回空数据")
                return {
                    "success": False,
                    "file_path": None,
                    "base64_data_uri": None,
                    "pil_image": None,
                    "error": f"下载失败: {asset_id}"
                }
            
            thumbnail_data = response_info['data']
            content_type = response_info.get('content_type', '')
            
            # 根据 Content-Type 或文件内容检测文件格式
            file_extension = _detect_image_format(thumbnail_data, content_type)
            
            task_end_time = time.time()
            total_duration = (task_end_time - task_start_time) * 1000
            
            if return_pil:
                # 返回 PIL Image 对象（性能最优：内存占用最小，无需编码/解码）
                pil_start_time = time.time()
                try:
                    from PIL import Image
                    from io import BytesIO
                    
                    # 将字节流转换为 PIL Image 对象
                    pil_image = Image.open(BytesIO(thumbnail_data))
                    
                    pil_end_time = time.time()
                    pil_duration = (pil_end_time - pil_start_time) * 1000
                    
                    logger.info(
                        f"[性能] {asset_id}: API耗时={api_duration:.2f}ms, PIL转换耗时={pil_duration:.2f}ms, 总耗时={total_duration:.2f}ms, 图片大小={len(thumbnail_data)} bytes"
                    )
                    
                    return {
                        "success": True,
                        "pil_image": pil_image,
                        "base64_data_uri": None,
                        "file_path": None,
                        "asset_id": asset_id,
                        "file_size": len(thumbnail_data),
                        "file_format": file_extension,
                        "content_type": content_type
                    }
                except Exception as e:
                    logger.error(f"[性能] 转换为 PIL Image 失败 {asset_id}: {e}")
                    # 降级到 base64
                    return_pil = False
                    return_base64 = True
            
            if return_base64:
                # 直接转换为 base64 data URI，不保存文件
                base64_start_time = time.time()
                # 确定 MIME 类型
                mime_type_map = {
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.png': 'image/png',
                    '.gif': 'image/gif',
                    '.webp': 'image/webp',
                    '.bmp': 'image/bmp'
                }
                mime_type = mime_type_map.get(file_extension.lower(), content_type or 'image/jpeg')
                
                # 转换为 base64
                base64_encoded = base64.b64encode(thumbnail_data).decode('utf-8')
                base64_data_uri = f"data:{mime_type};base64,{base64_encoded}"
                
                base64_end_time = time.time()
                base64_duration = (base64_end_time - base64_start_time) * 1000
                
                logger.debug(
                    f"[性能] {asset_id}: API耗时={api_duration:.2f}ms, base64编码耗时={base64_duration:.2f}ms, 总耗时={total_duration:.2f}ms"
                )
                
                return {
                    "success": True,
                    "base64_data_uri": base64_data_uri,
                    "pil_image": None,
                    "file_path": None,  # 不保存文件
                    "asset_id": asset_id,
                    "file_size": len(thumbnail_data),
                    "file_format": file_extension,
                    "content_type": content_type
                }
            else:
                # 保存文件（降级方案）
                if not save_dir:
                    return {
                        "success": False,
                        "file_path": None,
                        "base64_data_uri": None,
                        "error": f"save_dir 未提供，无法保存文件"
                    }
                
                size_suffix = thumbnail_size.value if thumbnail_size else "default"
                save_filename = f"{asset_id}_{size_suffix}{file_extension}"
                save_path = save_dir / save_filename
                
                # 保存文件（同步操作，但在并行任务中执行）
                save_start_time = time.time()
                with open(save_path, 'wb') as f:
                    f.write(thumbnail_data)
                save_end_time = time.time()
                save_duration = (save_end_time - save_start_time) * 1000
                
                total_duration_with_save = (save_end_time - task_start_time) * 1000
                
                logger.debug(
                    f"[性能] {asset_id}: API耗时={api_duration:.2f}ms, 保存耗时={save_duration:.2f}ms, 总耗时={total_duration_with_save:.2f}ms"
                )
                
                return {
                    "success": True,
                    "file_path": str(save_path),
                    "base64_data_uri": None,
                    "pil_image": None,
                    "asset_id": asset_id,
                    "file_size": len(thumbnail_data),
                    "file_format": file_extension,
                    "content_type": content_type
                }
            
        except Exception as e:
            task_end_time = time.time()
            total_duration = (task_end_time - task_start_time) * 1000
            logger.error(f"[性能] 下载缩略图失败 {asset_id}: {e}, 耗时: {total_duration:.2f}ms")
            return {
                "success": False,
                "file_path": None,
                "base64_data_uri": None,
                "pil_image": None,
                "error": f"{asset_id}: {str(e)}"
            }
    
    async def batch_download_thumbnails(
        self,
        asset_ids: List[str],
        save_dir: Union[str, Path] = None,
        thumbnail_size: AssetMediaSize = AssetMediaSize.THUMBNAIL,
        return_base64: bool = True,
        return_pil: bool = False
    ) -> Dict[str, any]:
        """
        批量下载指定资产的缩略图
        
        Args:
            asset_ids: 资产ID列表
            save_dir: 保存目录路径（可选，如果 return_base64=True 或 return_pil=True 则不需要）
            thumbnail_size: 缩略图尺寸
            return_base64: 是否返回 base64 data URI（True）或文件路径（False）
            return_pil: 是否返回 PIL Image 对象（优先级高于 return_base64，性能最优）
        
        Returns:
            包含下载结果的字典：
            - success: 是否成功
            - downloaded: 成功下载数量
            - failed: 失败数量
            - saved_files: 文件路径列表（return_base64=False 且 return_pil=False 时）
            - base64_data_uris: base64 data URI 列表（return_base64=True 且 return_pil=False 时）
            - pil_images: PIL Image 对象列表（return_pil=True 时）
            - errors: 错误列表
        
        性能对比（推荐使用 return_pil=True）：
        - PIL Image 对象：内存占用最小（原始大小），无需编码/解码，Gradio 直接使用，性能最优 ⭐⭐⭐⭐⭐
        - base64 data URI：内存占用增加约 33%，需要编码，Gradio 需要解析，性能中等 ⭐⭐⭐
        - 文件路径：需要文件 I/O，性能最差 ⭐⭐
        """
        if not self.api.enabled:
            return {
                "success": False,
                "downloaded": 0,
                "failed": 0,
                "saved_files": [],
                "base64_data_uris": [],
                "pil_images": [],
                "errors": ["Immich API未启用"]
            }
        
        # 如果不需要保存文件，save_dir 可以为 None
        save_path = Path(save_dir) if save_dir else None
        if save_path:
            save_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"[immich_logic] 开始批量下载缩略图: 共 {len(asset_ids)} 个资产, asset_ids={asset_ids}")
        
        result = {
            "success": False,
            "downloaded": 0,
            "failed": 0,
            "saved_files": [],
            "base64_data_uris": [],
            "pil_images": [],
            "errors": []
        }
        
        # 直接并行下载缩略图（不需要先获取资产信息，view_asset_with_info 会直接下载）
        # 这样可以最大化并行度，减少等待时间
        # 如果 return_pil=True，返回 PIL Image 对象（性能最优，推荐）
        # 如果 return_base64=True，不保存文件，直接返回 base64 data URI，避免文件 I/O 操作
        import time
        batch_start_time = time.time()
        
        logger.info(f"[immich_logic] 创建 {len(asset_ids)} 个下载任务... (return_pil={return_pil}, return_base64={return_base64})")
        task_creation_time = time.time()
        
        download_tasks = [
            self._download_single_thumbnail(
                asset_id=asset_id,
                asset_info=None,  # 不需要资产信息，直接下载
                save_dir=save_path,
                thumbnail_size=thumbnail_size,
                return_base64=return_base64,
                return_pil=return_pil
            )
            for asset_id in asset_ids
        ]
        
        # 并行执行所有下载任务
        download_start_time = time.time()
        logger.info(f"[immich_logic] 开始并行执行下载任务... (任务创建耗时: {(download_start_time - task_creation_time) * 1000:.2f}ms)")
        
        try:
            download_results = await asyncio.gather(*download_tasks, return_exceptions=True)
            download_end_time = time.time()
            download_duration = (download_end_time - download_start_time) * 1000
            logger.info(f"[immich_logic] 所有下载任务完成，共 {len(download_results)} 个结果, 并行下载耗时: {download_duration:.2f}ms (平均每张: {download_duration / len(asset_ids):.2f}ms)")
        except Exception as e:
            download_end_time = time.time()
            logger.error(f"[immich_logic] 并行下载异常: {e}", exc_info=True)
            download_results = []
        
        logger.info(f"[immich_logic] 开始处理下载结果...")
        for i, download_result in enumerate(download_results):
            asset_id = asset_ids[i] if i < len(asset_ids) else "unknown"
            if isinstance(download_result, Exception):
                result["failed"] += 1
                error_msg = f"{asset_id}: {str(download_result)}"
                result["errors"].append(error_msg)
                logger.error(f"[immich_logic] 下载任务异常 {asset_id}: {download_result}", exc_info=True)
            elif download_result and download_result.get("success"):
                result["downloaded"] += 1
                if return_pil:
                    # 优先返回 PIL Image 对象（性能最优）
                    pil_image = download_result.get("pil_image")
                    if pil_image:
                        result["pil_images"].append(pil_image)
                        logger.debug(f"[immich_logic] 成功下载 {asset_id} -> PIL Image 对象 (大小: {download_result.get('file_size', 0)} bytes)")
                    else:
                        result["failed"] += 1
                        result["errors"].append(f"{asset_id}: pil_image 为空")
                elif return_base64:
                    base64_data_uri = download_result.get("base64_data_uri")
                    if base64_data_uri:
                        result["base64_data_uris"].append(base64_data_uri)
                        logger.debug(f"[immich_logic] 成功下载 {asset_id} -> base64 data URI (大小: {download_result.get('file_size', 0)} bytes)")
                    else:
                        result["failed"] += 1
                        result["errors"].append(f"{asset_id}: base64_data_uri 为空")
                else:
                    file_path = download_result.get("file_path")
                    if file_path:
                        result["saved_files"].append(file_path)
                        logger.debug(f"[immich_logic] 成功下载 {asset_id} -> {file_path}")
                    else:
                        result["failed"] += 1
                        result["errors"].append(f"{asset_id}: file_path 为空")
            else:
                result["failed"] += 1
                error_msg = download_result.get("error", "未知错误") if download_result else "返回空结果"
                result["errors"].append(f"{asset_id}: {error_msg}")
                logger.warning(f"[immich_logic] 下载失败 {asset_id}: {error_msg}")
        
        result["success"] = result["downloaded"] > 0
        batch_end_time = time.time()
        total_duration = (batch_end_time - batch_start_time) * 1000
        
        # 计算各阶段耗时
        task_creation_duration = (task_creation_time - batch_start_time) * 1000
        download_duration = (download_end_time - download_start_time) * 1000
        result_processing_duration = (batch_end_time - download_end_time) * 1000
        
        logger.info(f"[immich_logic] ========== 批量下载性能统计 ==========")
        logger.info(f"[immich_logic] 任务创建耗时: {task_creation_duration:.2f}ms")
        logger.info(f"[immich_logic] 并行下载耗时: {download_duration:.2f}ms (平均每张: {download_duration / len(asset_ids):.2f}ms)")
        logger.info(f"[immich_logic] 结果处理耗时: {result_processing_duration:.2f}ms")
        logger.info(f"[immich_logic] 总耗时: {total_duration:.2f}ms")
        logger.info(f"[immich_logic] 成功率: {result['downloaded']}/{len(asset_ids)}, 失败: {result['failed']}")
        
        if return_pil:
            logger.info(f"[immich_logic] 返回 {len(result['pil_images'])} 个 PIL Image 对象（性能最优：内存占用最小，无需编码/解码）")
        elif return_base64:
            logger.info(f"[immich_logic] 返回 {len(result['base64_data_uris'])} 个 base64 data URI（未保存文件，避免文件 I/O）")
        
        logger.info(f"[immich_logic] =====================================")
        return result
    
    async def _download_with_info(
        self,
        asset_id: str,
        asset_info_task,
        save_dir: Path,
        thumbnail_size: AssetMediaSize
    ) -> Dict[str, any]:
        """下载缩略图（等待资产信息获取完成）"""
        try:
            asset_info = await asset_info_task
            if not asset_info:
                return {
                    "success": False,
                    "file_path": None,
                    "error": f"无法获取资产信息: {asset_id}"
                }
            
            return await self._download_single_thumbnail(
                asset_id=asset_id,
                asset_info=asset_info,
                save_dir=save_dir,
                thumbnail_size=thumbnail_size
            )
        except Exception as e:
            return {
                "success": False,
                "file_path": None,
                "error": f"{asset_id}: {str(e)}"
            }

