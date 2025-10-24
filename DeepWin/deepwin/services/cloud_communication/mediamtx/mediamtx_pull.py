# MediaMTX拉流类

import cv2
import time
import logging
import threading
from typing import Optional, Dict, Any

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MediaMTXPuller:
    """MediaMTX拉流器"""
    
    def __init__(self, server_host: str = '34.172.161.212', server_port: int = 8554):
        self.server_host = server_host
        self.server_port = server_port
        self.stream_name = 'camera_stream'
        self.rtsp_url = f'rtsp://{server_host}:{server_port}/{self.stream_name}'
        
        # 拉流状态
        self.is_playing = False
        self.cap: Optional[cv2.VideoCapture] = None
        
        # 统计信息
        self.frame_count = 0
        self.start_time = 0
        self.last_stats_time = 0
        self.connection_retry_count = 0
        self.max_retry_count = 5
        self.retry_delay = 3.0
        
        # 尝试不同的RTSP URL格式，优先使用TCP传输
        self.rtsp_urls = [
            self.rtsp_url + '?tcp',  # 优先使用TCP传输，更稳定
            self.rtsp_url,  # 原始URL作为备选
            self.rtsp_url + '?udp',  # UDP传输作为最后备选
        ]
        
    def set_stream_name(self, stream_name: str):
        """设置流名称"""
        self.stream_name = stream_name
        self.rtsp_url = f'rtsp://{self.server_host}:{self.server_port}/{stream_name}'
        self.rtsp_urls = [
            self.rtsp_url + '?tcp',
            self.rtsp_url,
            self.rtsp_url + '?udp',
        ]
        logger.info(f"🔧 流名称设置为: {stream_name}")
    
    def connect(self) -> bool:
        """连接到RTSP流"""
        for i, url in enumerate(self.rtsp_urls):
            try:
                logger.info(f"🔗 正在连接到RTSP流 (尝试 {i+1}/{len(self.rtsp_urls)}): {url}")
                
                # 创建VideoCapture对象
                self.cap = cv2.VideoCapture(url)
                
                # 设置缓冲区大小，减少延迟
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                
                # 设置超时时间（如果支持的话）
                try:
                    self.cap.set(cv2.CAP_PROP_TIMEOUT, 10000)  # 10秒超时
                except AttributeError:
                    # 静默处理，不显示警告，因为这不影响功能
                    pass
                
                # 测试连接
                if not self.cap.isOpened():
                    logger.warning(f"⚠️ 无法打开RTSP流: {url}")
                    continue
                
                # 尝试读取一帧来验证连接
                ret, frame = self.cap.read()
                if not ret or frame is None:
                    logger.warning(f"⚠️ 无法读取RTSP流数据: {url}")
                    self.cap.release()
                    continue
                
                height, width = frame.shape[:2]
                logger.info(f"✅ 成功连接到RTSP流: {width}x{height} (使用URL: {url})")
                self.connection_retry_count = 0
                return True
                
            except Exception as e:
                logger.warning(f"⚠️ 连接RTSP流失败 (URL: {url}): {e}")
                if self.cap:
                    self.cap.release()
                continue
        
        logger.error("❌ 所有RTSP连接尝试都失败了")
        return False
    
    def disconnect(self):
        """断开连接"""
        if self.cap:
            self.cap.release()
            logger.info("🔌 已断开RTSP连接")
            self.cap = None
    
    def reconnect(self) -> bool:
        """重新连接"""
        self.connection_retry_count += 1
        if self.connection_retry_count > self.max_retry_count:
            logger.error(f"❌ 重连次数超过限制 ({self.max_retry_count})")
            return False
        
        logger.info(f"🔄 尝试重新连接 ({self.connection_retry_count}/{self.max_retry_count})...")
        self.disconnect()
        time.sleep(self.retry_delay)
        return self.connect()
    
    def start_play(self, show_preview: bool = True, show_stats: bool = True):
        """开始播放RTSP视频流"""
        logger.info("🎬 开始播放RTSP视频流...")
        
        if not self.connect():
            logger.error("❌ 初始连接失败")
            return False
        
        self.is_playing = True
        self.frame_count = 0
        self.start_time = time.time()
        self.last_stats_time = self.start_time
        
        try:
            while self.is_playing:
                ret, frame = self.cap.read()
                
                if not ret or frame is None:
                    logger.warning("⚠️ 无法读取帧，尝试重连...")
                    if not self.reconnect():
                        logger.error("❌ 重连失败，停止播放")
                        break
                    continue
                
                # 重置重连计数
                self.connection_retry_count = 0
                
                # 显示视频帧
                if show_preview:
                    cv2.imshow('RTSP Video Stream', frame)
                
                # 检查用户输入
                if show_preview:
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        logger.info("🛑 用户停止播放")
                        break
                    elif key == ord('r'):
                        logger.info("🔄 用户请求重连")
                        if not self.reconnect():
                            break
                
                self.frame_count += 1
                
                # 显示统计信息
                if show_stats:
                    current_time = time.time()
                    if current_time - self.last_stats_time >= 5.0:  # 每5秒显示一次
                        elapsed = current_time - self.start_time
                        fps = self.frame_count / elapsed if elapsed > 0 else 0
                        logger.info(f"📊 已播放 {self.frame_count} 帧, 平均FPS: {fps:.1f}")
                        self.last_stats_time = current_time
                
        except KeyboardInterrupt:
            logger.info("🛑 用户中断播放")
        except Exception as e:
            logger.error(f"❌ 播放异常: {e}")
        finally:
            self.is_playing = False
            self.disconnect()
            if show_preview:
                cv2.destroyAllWindows()
            logger.info("🏁 播放结束")
        
        return True
    
    def stop_play(self):
        """停止播放"""
        self.is_playing = False
    
    def get_stats(self) -> Dict[str, Any]:
        """获取播放统计信息"""
        if not self.is_playing:
            return {}
        
        current_time = time.time()
        elapsed = current_time - self.start_time
        
        stats = {
            'is_playing': self.is_playing,
            'elapsed_time': elapsed,
            'rtsp_url': self.rtsp_url,
            'frame_count': self.frame_count,
            'average_fps': self.frame_count / elapsed if elapsed > 0 else 0,
            'connection_retry_count': self.connection_retry_count,
            'max_retry_count': self.max_retry_count
        }
        
        return stats

def test_rtsp_connection(rtsp_url: str) -> bool:
    """测试RTSP连接"""
    logger.info(f"🔍 测试RTSP连接: {rtsp_url}")
    
    try:
        cap = cv2.VideoCapture(rtsp_url)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        # 设置超时时间（如果支持的话）
        try:
            cap.set(cv2.CAP_PROP_TIMEOUT, 5000)  # 5秒超时
        except AttributeError:
            # 静默处理，不显示警告
            pass
    
        if not cap.isOpened():
            logger.error("❌ RTSP连接测试失败")
            return False
        
        ret, frame = cap.read()
        cap.release()
        
        if ret and frame is not None:
            height, width = frame.shape[:2]
            logger.info(f"✅ RTSP连接测试成功: {width}x{height}")
            return True
        else:
            logger.error("❌ RTSP流数据读取失败")
            return False
            
    except Exception as e:
        logger.error(f"❌ RTSP连接测试异常: {e}")
        return False

def main():
    """测试函数"""
    logger.info("=== MediaMTX拉流器测试 ===")
    
    # 创建拉流器
    puller = MediaMTXPuller()
    
    # 测试RTSP连接
    if not test_rtsp_connection(puller.rtsp_url):
        logger.error("❌ RTSP连接测试失败，请检查服务器状态")
        return
    
    try:
        # 开始播放
        success = puller.start_play(show_preview=True, show_stats=True)
        
        if success:
            logger.info("✅ 播放完成")
        else:
            logger.error("❌ 播放失败")
    
    except Exception as e:
        logger.error(f"❌ 程序异常: {e}")
    finally:
        puller.stop_play()

if __name__ == "__main__":
    main()
