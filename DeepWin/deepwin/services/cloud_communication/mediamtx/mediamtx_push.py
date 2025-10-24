# MediaMTX推流类

import cv2
import subprocess
import time
import platform
import logging
import threading
from typing import Optional, Dict, Any

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MediaMTXPusher:
    """MediaMTX推流器"""
    
    def __init__(self, server_host: str = '34.172.161.212', server_port: int = 8554):
        self.server_host = server_host
        self.server_port = server_port
        self.stream_name = 'camera_stream'
        self.rtsp_url = f'rtsp://{server_host}:{server_port}/{self.stream_name}'
        
        # 推流状态
        self.is_streaming = False
        self.process: Optional[subprocess.Popen] = None
        self.camera: Optional[cv2.VideoCapture] = None
        
        # 推流参数
        self.frame_width = 640
        self.frame_height = 480
        self.fps = 30
        self.bitrate = '1000k'
        self.crf = 23
        
        # 统计信息
        self.frame_count = 0
        self.start_time = 0
        self.last_stats_time = 0
        
    def set_stream_params(self, width: int = 640, height: int = 480, fps: int = 30, 
                         bitrate: str = '1000k', crf: int = 23):
        """设置推流参数"""
        self.frame_width = width
        self.frame_height = height
        self.fps = fps
        self.bitrate = bitrate
        self.crf = crf
        logger.info(f"🔧 推流参数设置: {width}x{height}@{fps}fps, bitrate={bitrate}, crf={crf}")
    
    def test_camera(self, camera_index: int = 0) -> bool:
        """测试摄像头是否可用"""
        logger.info(f"🔍 测试摄像头 {camera_index}...")
        
        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            logger.error(f"❌ 摄像头 {camera_index} 不可用")
            return False
        
        ret, frame = cap.read()
        if ret and frame is not None:
            height, width = frame.shape[:2]
            logger.info(f"✅ 摄像头 {camera_index} 可用: {width}x{height}")
            cap.release()
            return True
        else:
            logger.error(f"❌ 摄像头 {camera_index} 无法读取帧")
            cap.release()
            return False
    
    def get_directshow_devices(self) -> Dict[int, str]:
        """获取Windows DirectShow设备列表"""
        if platform.system() != 'Windows':
            return {}
        
        try:
            result = subprocess.run([
                'ffmpeg', '-f', 'dshow', '-list_devices', 'true', '-i', 'dummy'
            ], capture_output=True, text=True, timeout=10)
            
            devices = {}
            lines = result.stdout.split('\n')
            in_video_section = False
            
            for line in lines:
                if '[dshow @' in line and 'DirectShow video devices' in line:
                    in_video_section = True
                    continue
                elif '[dshow @' in line and 'DirectShow audio devices' in line:
                    in_video_section = False
                    continue
                
                if in_video_section and '"' in line:
                    import re
                    match = re.search(r'"([^"]+)"', line)
                    if match:
                        device_name = match.group(1)
                        index_match = re.search(r'\[(\d+)\]', line)
                        if index_match:
                            index = int(index_match.group(1))
                            devices[index] = device_name
            
            return devices
        except Exception as e:
            logger.warning(f"⚠️ 获取DirectShow设备列表失败: {e}")
            return {}
    
    def start_stream_direct(self, camera_index: int = 0) -> bool:
        """使用FFmpeg直接推流"""
        logger.info(f"🎬 开始直接推流 (摄像头 {camera_index})...")
        
        # 构建FFmpeg命令
        if platform.system() == 'Windows':
            # 尝试获取DirectShow设备名称
            devices = self.get_directshow_devices()
            if camera_index in devices:
                input_source = f'video={devices[camera_index]}'
                logger.info(f"📹 使用DirectShow设备: {devices[camera_index]}")
            else:
                input_source = f'video={camera_index}'
                logger.info(f"📹 使用摄像头索引: {camera_index}")
            
            ffmpeg_cmd = [
                'ffmpeg',
                '-f', 'dshow',
                '-i', input_source,
                '-vcodec', 'libx264',
                '-preset', 'ultrafast',
                '-tune', 'zerolatency',
                '-crf', str(self.crf),
                '-pix_fmt', 'yuv420p',
                '-s', f'{self.frame_width}x{self.frame_height}',
                '-r', str(self.fps),
                '-g', str(self.fps),  # GOP大小
                '-keyint_min', str(self.fps // 2),  # 最小关键帧间隔
                '-f', 'rtsp',
                '-rtsp_transport', 'tcp',
                self.rtsp_url
            ]
        else:
            # Linux/macOS
            input_format = 'v4l2' if platform.system() == 'Linux' else 'avfoundation'
            ffmpeg_cmd = [
                'ffmpeg',
                '-f', input_format,
                '-i', str(camera_index),
                '-vcodec', 'libx264',
                '-preset', 'ultrafast',
                '-tune', 'zerolatency',
                '-crf', str(self.crf),
                '-pix_fmt', 'yuv420p',
                '-s', f'{self.frame_width}x{self.frame_height}',
                '-r', str(self.fps),
                '-g', str(self.fps),
                '-keyint_min', str(self.fps // 2),
                '-f', 'rtsp',
                '-rtsp_transport', 'tcp',
                self.rtsp_url
            ]
        
        try:
            logger.info(f"🚀 启动FFmpeg推流到: {self.rtsp_url}")
            self.process = subprocess.Popen(ffmpeg_cmd, 
                                          stdout=subprocess.PIPE, 
                                          stderr=subprocess.PIPE,
                                          text=True)
            
            self.is_streaming = True
            self.start_time = time.time()
            self.last_stats_time = self.start_time
            
            # 监控进程
            while self.is_streaming:
                if self.process.poll() is not None:
                    # 进程已结束
                    stdout, stderr = self.process.communicate()
                    logger.error(f"❌ FFmpeg进程结束，退出码: {self.process.returncode}")
                    if stderr:
                        logger.error(f"错误信息: {stderr}")
                    self.is_streaming = False
                    break
                
                # 显示统计信息
                current_time = time.time()
                if current_time - self.last_stats_time >= 5.0:
                    elapsed = current_time - self.start_time
                    logger.info(f"📊 推流运行时间: {elapsed:.1f}秒")
                    self.last_stats_time = current_time
                
                time.sleep(1)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 直接推流失败: {e}")
            self.is_streaming = False
            return False
    
    def start_stream_pipeline(self, camera_index: int = 0) -> bool:
        """使用OpenCV+FFmpeg管道推流"""
        logger.info(f"🎬 开始管道推流 (摄像头 {camera_index})...")
        
        # 打开摄像头
        self.camera = cv2.VideoCapture(camera_index)
        if not self.camera.isOpened():
            logger.error(f"❌ 无法打开摄像头 {camera_index}")
            return False
        
        # 设置摄像头参数
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
        self.camera.set(cv2.CAP_PROP_FPS, self.fps)
        
        # 创建FFmpeg命令
        ffmpeg_cmd = [
            'ffmpeg',
            '-f', 'rawvideo',
            '-pix_fmt', 'bgr24',
            '-s', f'{self.frame_width}x{self.frame_height}',
            '-r', str(self.fps),
            '-i', 'pipe:',
            '-c:v', 'libx264',
            '-preset', 'ultrafast',
            '-tune', 'zerolatency',
            '-crf', str(self.crf),
            '-pix_fmt', 'yuv420p',
            '-g', str(self.fps),
            '-keyint_min', str(self.fps // 2),
            '-f', 'rtsp',
            '-rtsp_transport', 'tcp',
            self.rtsp_url
        ]
        
        try:
            logger.info(f"🚀 启动FFmpeg管道推流到: {self.rtsp_url}")
            self.process = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)
            
            self.is_streaming = True
            self.frame_count = 0
            self.start_time = time.time()
            self.last_stats_time = self.start_time
            
            logger.info("📹 开始推流...")
            
            while self.is_streaming:
                ret, frame = self.camera.read()
                if not ret:
                    logger.error("❌ 无法读取摄像头帧")
                    break
                
                # 调整帧大小
                frame = cv2.resize(frame, (self.frame_width, self.frame_height))
                
                try:
                    # 发送帧到FFmpeg
                    self.process.stdin.write(frame.tobytes())
                    self.process.stdin.flush()
                    
                    self.frame_count += 1
                    
                    # 显示统计信息
                    current_time = time.time()
                    if current_time - self.last_stats_time >= 5.0:
                        elapsed = current_time - self.start_time
                        fps = self.frame_count / elapsed if elapsed > 0 else 0
                        logger.info(f"📊 已推流 {self.frame_count} 帧, 平均FPS: {fps:.1f}")
                        self.last_stats_time = current_time
                    
                except BrokenPipeError:
                    logger.error("❌ FFmpeg管道断开")
                    break
                except Exception as e:
                    logger.error(f"❌ 发送帧失败: {e}")
                    break
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 管道推流失败: {e}")
            self.is_streaming = False
            return False
    
    def start_stream(self, camera_index: int = 0, method: str = 'pipeline') -> bool:
        """开始推流
        
        Args:
            camera_index: 摄像头索引
            method: 推流方法 ('direct' 或 'pipeline')
        """
        if self.is_streaming:
            logger.warning("⚠️ 推流已在进行中")
            return False
        
        # 测试摄像头
        if not self.test_camera(camera_index):
            return False
        
        logger.info(f"🎬 开始推流到MediaMTX服务器: {self.rtsp_url}")
        logger.info(f"📹 推流方法: {method}")
        
        if method == 'direct':
            return self.start_stream_direct(camera_index)
        elif method == 'pipeline':
            return self.start_stream_pipeline(camera_index)
        else:
            logger.error(f"❌ 不支持的推流方法: {method}")
            return False
    
    def stop_stream(self):
        """停止推流"""
        if not self.is_streaming:
            logger.warning("⚠️ 推流未在进行中")
            return
        
        logger.info("🛑 停止推流...")
        self.is_streaming = False
        
        # 停止FFmpeg进程
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except:
                self.process.kill()
            self.process = None
        
        # 释放摄像头
        if self.camera:
            self.camera.release()
            self.camera = None
        
        logger.info("🏁 推流已停止")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取推流统计信息"""
        if not self.is_streaming:
            return {}
        
        current_time = time.time()
        elapsed = current_time - self.start_time
        
        stats = {
            'is_streaming': self.is_streaming,
            'elapsed_time': elapsed,
            'rtsp_url': self.rtsp_url,
            'frame_count': self.frame_count,
            'average_fps': self.frame_count / elapsed if elapsed > 0 else 0,
            'resolution': f'{self.frame_width}x{self.frame_height}',
            'fps': self.fps,
            'bitrate': self.bitrate,
            'crf': self.crf
        }
        
        return stats

def main():
    """测试函数"""
    logger.info("=== MediaMTX推流器测试 ===")
    
    # 创建推流器
    pusher = MediaMTXPusher()
    
    # 设置推流参数
    pusher.set_stream_params(width=640, height=480, fps=30, crf=23)
    
    try:
        # 开始推流（使用管道方法，更稳定）
        success = pusher.start_stream(camera_index=0, method='pipeline')
        
        if success:
            logger.info("✅ 推流启动成功")
            logger.info("按 Ctrl+C 停止推流")
            
            # 保持运行
            while pusher.is_streaming:
                time.sleep(1)
        else:
            logger.error("❌ 推流启动失败")
    
    except KeyboardInterrupt:
        logger.info("🛑 用户中断")
    except Exception as e:
        logger.error(f"❌ 程序异常: {e}")
    finally:
        pusher.stop_stream()

if __name__ == "__main__":
    main()
