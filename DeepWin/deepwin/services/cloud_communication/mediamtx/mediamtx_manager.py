# MediaMTX管理器

import time
import logging
import threading
from typing import Optional, Dict, Any, List
from mediamtx_push import MediaMTXPusher
from mediamtx_pull import MediaMTXPuller

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MediaMTXManager:
    """MediaMTX流媒体管理器"""
    
    def __init__(self, server_host: str = '35.192.64.247', server_port: int = 8554):
        self.server_host = server_host
        self.server_port = server_port
        
        # 推流器
        self.pusher: Optional[MediaMTXPusher] = None
        self.pusher_thread: Optional[threading.Thread] = None
        
        # 拉流器列表
        self.pullers: List[MediaMTXPuller] = []
        self.puller_threads: List[threading.Thread] = []
        
        # 管理状态
        self.is_running = False
        self.auto_reconnect = True
        self.monitor_interval = 10.0  # 监控间隔（秒）
        
    def create_pusher(self, stream_name: str = 'camera_stream') -> MediaMTXPusher:
        """创建推流器"""
        pusher = MediaMTXPusher(self.server_host, self.server_port)
        pusher.stream_name = stream_name
        pusher.rtsp_url = f'rtsp://{self.server_host}:{self.server_port}/{stream_name}'
        return pusher
    
    def create_puller(self, stream_name: str = 'camera_stream') -> MediaMTXPuller:
        """创建拉流器"""
        puller = MediaMTXPuller(self.server_host, self.server_port)
        puller.set_stream_name(stream_name)
        return puller
    
    def start_push(self, camera_index: int = 0, stream_name: str = 'camera_stream', 
                   method: str = 'pipeline', **kwargs) -> bool:
        """启动推流"""
        if self.pusher and self.pusher.is_streaming:
            logger.warning("⚠️ 推流已在进行中")
            return False
        
        logger.info(f"🚀 启动推流: {stream_name}")
        
        # 创建推流器
        self.pusher = self.create_pusher(stream_name)
        
        # 设置推流参数
        if kwargs:
            self.pusher.set_stream_params(**kwargs)
        
        # 在单独线程中启动推流
        def push_worker():
            try:
                success = self.pusher.start_stream(camera_index, method)
                if not success:
                    logger.error("❌ 推流启动失败")
            except Exception as e:
                logger.error(f"❌ 推流异常: {e}")
        
        self.pusher_thread = threading.Thread(target=push_worker, daemon=True)
        self.pusher_thread.start()
        
        # 等待推流启动
        time.sleep(2)
        
        if self.pusher.is_streaming:
            logger.info("✅ 推流启动成功")
            return True
        else:
            logger.error("❌ 推流启动失败")
            return False
    
    def stop_push(self):
        """停止推流"""
        if self.pusher:
            logger.info("🛑 停止推流...")
            self.pusher.stop_stream()
            self.pusher = None
            self.pusher_thread = None
            logger.info("✅ 推流已停止")
    
    def start_pull(self, stream_name: str = 'camera_stream', 
                   show_preview: bool = True, show_stats: bool = True) -> bool:
        """启动拉流"""
        logger.info(f"📺 启动拉流: {stream_name}")
        
        # 创建拉流器
        puller = self.create_puller(stream_name)
        self.pullers.append(puller)
        
        # 在单独线程中启动拉流
        def pull_worker():
            try:
                success = puller.start_play(show_preview, show_stats)
                if not success:
                    logger.error(f"❌ 拉流启动失败: {stream_name}")
            except Exception as e:
                logger.error(f"❌ 拉流异常: {e}")
        
        puller_thread = threading.Thread(target=pull_worker, daemon=True)
        self.puller_threads.append(puller_thread)
        puller_thread.start()
        
        # 等待拉流启动
        time.sleep(2)
        
        if puller.is_playing:
            logger.info(f"✅ 拉流启动成功: {stream_name}")
            return True
        else:
            logger.error(f"❌ 拉流启动失败: {stream_name}")
            return False
    
    def stop_pull(self, stream_name: str = None):
        """停止拉流"""
        if stream_name:
            # 停止指定流
            for i, puller in enumerate(self.pullers):
                if puller.stream_name == stream_name:
                    logger.info(f"🛑 停止拉流: {stream_name}")
                    puller.stop_play()
                    self.pullers.pop(i)
                    if i < len(self.puller_threads):
                        self.puller_threads.pop(i)
                    logger.info(f"✅ 拉流已停止: {stream_name}")
                    return
            logger.warning(f"⚠️ 未找到拉流: {stream_name}")
        else:
            # 停止所有拉流
            logger.info("🛑 停止所有拉流...")
            for puller in self.pullers:
                puller.stop_play()
            self.pullers.clear()
            self.puller_threads.clear()
            logger.info("✅ 所有拉流已停止")
    
    def start_monitoring(self):
        """启动监控"""
        if self.is_running:
            logger.warning("⚠️ 监控已在进行中")
            return
        
        self.is_running = True
        logger.info("🔍 启动监控...")
        
        def monitor_worker():
            while self.is_running:
                try:
                    # 监控推流状态
                    if self.pusher and not self.pusher.is_streaming:
                        logger.warning("⚠️ 推流已断开")
                        if self.auto_reconnect:
                            logger.info("🔄 尝试重新启动推流...")
                            # 这里可以实现自动重连逻辑
                    
                    # 监控拉流状态
                    for puller in self.pullers:
                        if not puller.is_playing:
                            logger.warning(f"⚠️ 拉流已断开: {puller.stream_name}")
                            if self.auto_reconnect:
                                logger.info(f"🔄 尝试重新启动拉流: {puller.stream_name}")
                                # 这里可以实现自动重连逻辑
                    
                    time.sleep(self.monitor_interval)
                    
                except Exception as e:
                    logger.error(f"❌ 监控异常: {e}")
                    time.sleep(self.monitor_interval)
        
        monitor_thread = threading.Thread(target=monitor_worker, daemon=True)
        monitor_thread.start()
    
    def stop_monitoring(self):
        """停止监控"""
        self.is_running = False
        logger.info("🛑 停止监控")
    
    def get_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        status = {
            'server': {
                'host': self.server_host,
                'port': self.server_port
            },
            'push': {
                'is_streaming': self.pusher.is_streaming if self.pusher else False,
                'stats': self.pusher.get_stats() if self.pusher else {}
            },
            'pull': {
                'count': len(self.pullers),
                'streams': []
            },
            'monitoring': {
                'is_running': self.is_running,
                'auto_reconnect': self.auto_reconnect,
                'monitor_interval': self.monitor_interval
            }
        }
        
        # 添加拉流信息
        for puller in self.pullers:
            stream_info = {
                'stream_name': puller.stream_name,
                'is_playing': puller.is_playing,
                'stats': puller.get_stats()
            }
            status['pull']['streams'].append(stream_info)
        
        return status
    
    def print_status(self):
        """打印系统状态"""
        status = self.get_status()
        
        print("\n" + "="*50)
        print("📊 MediaMTX系统状态")
        print("="*50)
        
        print(f"🖥️  服务器: {status['server']['host']}:{status['server']['port']}")
        
        print(f"\n📤 推流状态:")
        if status['push']['is_streaming']:
            stats = status['push']['stats']
            print(f"  ✅ 正在推流")
            print(f"  📹 分辨率: {stats.get('resolution', 'N/A')}")
            print(f"  🎯 FPS: {stats.get('fps', 'N/A')}")
            print(f"  📊 平均FPS: {stats.get('average_fps', 0):.1f}")
            print(f"  ⏱️  运行时间: {stats.get('elapsed_time', 0):.1f}秒")
        else:
            print(f"  ❌ 未推流")
        
        print(f"\n📥 拉流状态:")
        print(f"  📺 拉流数量: {status['pull']['count']}")
        for stream in status['pull']['streams']:
            if stream['is_playing']:
                stats = stream['stats']
                print(f"  ✅ {stream['stream_name']}: 平均FPS {stats.get('average_fps', 0):.1f}")
            else:
                print(f"  ❌ {stream['stream_name']}: 未播放")
        
        print(f"\n🔍 监控状态:")
        print(f"  {'✅' if status['monitoring']['is_running'] else '❌'} 监控运行中")
        print(f"  {'✅' if status['monitoring']['auto_reconnect'] else '❌'} 自动重连")
        print(f"  ⏱️  监控间隔: {status['monitoring']['monitor_interval']}秒")
        
        print("="*50)
    
    def cleanup(self):
        """清理资源"""
        logger.info("🧹 清理资源...")
        
        # 停止监控
        self.stop_monitoring()
        
        # 停止推流
        self.stop_push()
        
        # 停止所有拉流
        self.stop_pull()
        
        logger.info("✅ 资源清理完成")

def main():
    """测试函数"""
    logger.info("=== MediaMTX管理器测试 ===")
    
    # 创建管理器
    manager = MediaMTXManager()
    
    try:
        # 启动推流
        print("1. 启动推流...")
        push_success = manager.start_push(
            camera_index=0,
            stream_name='camera_stream',
            method='pipeline',
            width=640,
            height=480,
            fps=30,
            crf=23
        )
        
        if push_success:
            print("✅ 推流启动成功")
            
            # 等待推流稳定
            time.sleep(3)
            
            # 启动拉流
            print("2. 启动拉流...")
            pull_success = manager.start_pull(
                stream_name='camera_stream',
                show_preview=True,
                show_stats=True
            )
            
            if pull_success:
                print("✅ 拉流启动成功")
                
                # 启动监控
                print("3. 启动监控...")
                manager.start_monitoring()
                
                # 显示状态
                manager.print_status()
                
                print("\n按 Ctrl+C 停止...")
                
                # 保持运行
                while True:
                    time.sleep(5)
                    manager.print_status()
            else:
                print("❌ 拉流启动失败")
        else:
            print("❌ 推流启动失败")
    
    except KeyboardInterrupt:
        print("\n🛑 用户中断")
    except Exception as e:
        logger.error(f"❌ 程序异常: {e}")
    finally:
        manager.cleanup()

if __name__ == "__main__":
    main()
