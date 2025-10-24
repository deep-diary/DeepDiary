# 从摄像头获取视频流，以jpeg格式发送给TCP服务器34.172.161.212:8080

import cv2
import socket
import struct
import time
import threading
import logging
import json
import os
from typing import Optional, Tuple, Dict, Any

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 默认配置
DEFAULT_CONFIG = {
    "server": {
        "host": "34.172.161.212",
        "port": 8080
    },
    "camera": {
        "width": 640,
        "height": 480,
        "fps": 30,
        "jpeg_quality": 80
    },
    "connection": {
        "max_retry_count": 3,
        "retry_delay": 2.0,
        "timeout": 10
    }
}

def load_config(config_file: str = "tcp_client_config.json") -> Dict[str, Any]:
    """加载配置文件"""
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                logger.info(f"✅ 已加载配置文件: {config_file}")
                return config
        except Exception as e:
            logger.warning(f"⚠️ 加载配置文件失败: {e}，使用默认配置")
    else:
        logger.info("📝 配置文件不存在，使用默认配置")
    
    return DEFAULT_CONFIG

def save_config(config: Dict[str, Any], config_file: str = "tcp_client_config.json"):
    """保存配置文件"""
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        logger.info(f"💾 配置已保存到: {config_file}")
    except Exception as e:
        logger.error(f"❌ 保存配置文件失败: {e}")

class TCPVideoClient:
    """TCP视频流客户端"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        # 加载配置
        if config is None:
            config = load_config()
        
        # 服务器配置
        server_config = config.get("server", DEFAULT_CONFIG["server"])
        self.server_host = server_config.get("host", DEFAULT_CONFIG["server"]["host"])
        self.server_port = server_config.get("port", DEFAULT_CONFIG["server"]["port"])
        
        # 摄像头配置
        camera_config = config.get("camera", DEFAULT_CONFIG["camera"])
        self.frame_width = camera_config.get("width", DEFAULT_CONFIG["camera"]["width"])
        self.frame_height = camera_config.get("height", DEFAULT_CONFIG["camera"]["height"])
        self.fps = camera_config.get("fps", DEFAULT_CONFIG["camera"]["fps"])
        self.jpeg_quality = camera_config.get("jpeg_quality", DEFAULT_CONFIG["camera"]["jpeg_quality"])
        
        # 连接配置
        connection_config = config.get("connection", DEFAULT_CONFIG["connection"])
        self.max_retry_count = connection_config.get("max_retry_count", DEFAULT_CONFIG["connection"]["max_retry_count"])
        self.retry_delay = connection_config.get("retry_delay", DEFAULT_CONFIG["connection"]["retry_delay"])
        self.timeout = connection_config.get("timeout", DEFAULT_CONFIG["connection"]["timeout"])
        
        # 运行时状态
        self.socket: Optional[socket.socket] = None
        self.camera: Optional[cv2.VideoCapture] = None
        self.is_streaming = False
        
        logger.info(f"🔧 客户端配置: {self.server_host}:{self.server_port}, {self.frame_width}x{self.frame_height}@{self.fps}fps")
        
    def connect(self) -> bool:
        """连接到TCP服务器"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.timeout)
            self.socket.connect((self.server_host, self.server_port))
            logger.info(f"✅ 成功连接到服务器 {self.server_host}:{self.server_port}")
            return True
        except Exception as e:
            logger.error(f"❌ 连接服务器失败: {e}")
            return False
    
    def disconnect(self):
        """断开连接"""
        if self.socket:
            try:
                self.socket.close()
                logger.info("🔌 已断开服务器连接")
            except:
                pass
            self.socket = None
    
    def setup_camera(self, camera_index: int = 0) -> bool:
        """设置摄像头"""
        try:
            self.camera = cv2.VideoCapture(camera_index)
            if not self.camera.isOpened():
                logger.error(f"❌ 无法打开摄像头 {camera_index}")
                return False
            
            # 设置摄像头参数
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
            self.camera.set(cv2.CAP_PROP_FPS, self.fps)
            
            # 验证设置
            actual_width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = self.camera.get(cv2.CAP_PROP_FPS)
            
            logger.info(f"📹 摄像头设置: {actual_width}x{actual_height} @ {actual_fps:.1f}fps")
            return True
            
        except Exception as e:
            logger.error(f"❌ 设置摄像头失败: {e}")
            return False
    
    def release_camera(self):
        """释放摄像头"""
        if self.camera:
            self.camera.release()
            logger.info("📹 已释放摄像头")
            self.camera = None
    
    def encode_frame_to_jpeg(self, frame) -> bytes:
        """将帧编码为JPEG格式"""
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.jpeg_quality]
        _, jpeg_data = cv2.imencode('.jpg', frame, encode_param)
        return jpeg_data.tobytes()
    
    def send_frame(self, frame_data: bytes) -> bool:
        """发送帧数据到服务器"""
        for attempt in range(self.max_retry_count):
            try:
                if not self.socket:
                    return False
                
                # 发送帧大小（4字节）
                frame_size = len(frame_data)
                size_bytes = struct.pack('!I', frame_size)
                self.socket.sendall(size_bytes)
                
                # 发送帧数据
                self.socket.sendall(frame_data)
                return True
                
            except Exception as e:
                logger.warning(f"⚠️ 发送帧失败 (尝试 {attempt + 1}/{self.max_retry_count}): {e}")
                if attempt < self.max_retry_count - 1:
                    # 尝试重连
                    if self.reconnect():
                        continue
                    else:
                        time.sleep(self.retry_delay)
                else:
                    logger.error(f"❌ 发送帧最终失败: {e}")
                    return False
        return False
    
    def reconnect(self) -> bool:
        """重新连接到服务器"""
        logger.info("🔄 尝试重新连接...")
        self.disconnect()
        time.sleep(1.0)  # 等待1秒
        return self.connect()
    
    def stream_video(self, camera_index: int = 0, show_preview: bool = True):
        """开始视频流传输"""
        logger.info("🎬 开始视频流传输...")
        
        # 设置摄像头
        if not self.setup_camera(camera_index):
            return
        
        # 连接到服务器
        if not self.connect():
            self.release_camera()
            return
        
        self.is_streaming = True
        frame_count = 0
        start_time = time.time()
        last_stats_time = start_time
        
        try:
            while self.is_streaming:
                ret, frame = self.camera.read()
                if not ret:
                    logger.error("❌ 无法读取摄像头帧")
                    break
                
                # 调整帧大小
                frame = cv2.resize(frame, (self.frame_width, self.frame_height))
                
                # 编码为JPEG
                jpeg_data = self.encode_frame_to_jpeg(frame)
                
                # 发送到服务器
                if not self.send_frame(jpeg_data):
                    logger.error("❌ 发送帧失败，停止流传输")
                    break
                
                frame_count += 1
                
                # 显示预览
                if show_preview:
                    cv2.imshow('TCP Video Stream', frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        logger.info("🛑 用户停止流传输")
                        break
                
                # 统计信息
                current_time = time.time()
                if current_time - last_stats_time >= 5.0:  # 每5秒显示一次统计
                    elapsed = current_time - start_time
                    fps = frame_count / elapsed
                    logger.info(f"📊 已发送 {frame_count} 帧, 平均FPS: {fps:.1f}")
                    last_stats_time = current_time
                
                # 控制帧率
                time.sleep(1.0 / self.fps)
                
        except KeyboardInterrupt:
            logger.info("🛑 用户中断流传输")
        except Exception as e:
            logger.error(f"❌ 流传输异常: {e}")
        finally:
            self.is_streaming = False
            self.disconnect()
            self.release_camera()
            if show_preview:
                cv2.destroyAllWindows()
            logger.info("🏁 视频流传输结束")

def test_camera_devices():
    """测试可用的摄像头设备"""
    logger.info("🔍 正在检测可用的摄像头设备...")
    available_cameras = []
    
    for i in range(5):  # 检查前5个设备
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                height, width = frame.shape[:2]
                logger.info(f"✅ 摄像头 {i}: {width}x{height}")
                available_cameras.append(i)
            cap.release()
        else:
            logger.info(f"❌ 摄像头 {i}: 不可用")
    
    return available_cameras

def main():
    """主函数"""
    logger.info("=== TCP视频流客户端 ===")
    
    # 检测可用摄像头
    cameras = test_camera_devices()
    
    if not cameras:
        logger.error("❌ 没有找到可用的摄像头设备")
        return
    
    # 选择摄像头
    if len(cameras) == 1:
        camera_index = cameras[0]
        logger.info(f"📹 使用摄像头 {camera_index}")
    else:
        logger.info(f"📹 找到多个摄像头: {cameras}")
        try:
            camera_index = int(input("请选择摄像头编号: "))
            if camera_index not in cameras:
                logger.error(f"❌ 摄像头 {camera_index} 不可用")
                return
        except ValueError:
            logger.error("❌ 无效的输入")
            return
    
    # 创建TCP客户端
    client = TCPVideoClient()
    
    try:
        # 开始视频流传输
        client.stream_video(camera_index, show_preview=True)
    except Exception as e:
        logger.error(f"❌ 程序异常: {e}")

if __name__ == "__main__":
    main()