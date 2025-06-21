# src/app_logic/device_logic_manager/devices/deep_arm/teaching_trajectory_manager.py
# DeepMotor 示教轨迹录制、存储和播放管理

import time
import json
import os
from datetime import datetime
from PySide6.QtCore import QObject, Signal, Slot, QTimer
from typing import Dict, Any, List, Callable, Optional
import numpy as np

from src.data_management.log_manager import LogManager
from .robot_trajectory import RobotTrajectory


class TeachingTrajectoryManager(QObject):
    """
    管理 DeepMotor 示教轨迹的录制、存储和播放逻辑。
    支持响应式示教，实时记录电机位置和速度信息。
    """
    # 示教相关信号 (用于通知 DeviceLogicManager)
    _trajectory_recorded = Signal(str, str, list) # (device_id, trajectory_name, trajectory_points)
    _playback_progress = Signal(str, int) # (device_id, progress_percentage)
    _teaching_status_changed = Signal(str, bool) # (device_id, is_teaching)
    _record_point_requested = Signal(str) # (device_id) 请求记录当前点
    
    # 新增：轨迹播放相关信号
    _trajectory_point_ready = Signal(str, float, float) # (device_id, position, velocity) 轨迹点就绪信号
    _trajectory_playback_started = Signal(str, str) # (device_id, trajectory_name) 轨迹播放开始
    _trajectory_playback_finished = Signal(str, str) # (device_id, trajectory_name) 轨迹播放完成
    _trajectory_playback_error = Signal(str, str) # (device_id, error_message) 轨迹播放错误

    def __init__(self, log_manager: LogManager, trajectory_folder: str = None, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.logger = log_manager.get_logger(__name__)
        self.logger.info("TeachingTrajectoryManager: 初始化中...")
        
        # 示教状态管理
        self._teaching_sessions: Dict[str, bool] = {} # {device_id: is_teaching}
        self._recording_sessions: Dict[str, List[Dict[str, Any]]] = {} # {device_id: [trajectory_points]}
        self._stored_trajectories: Dict[str, Dict[str, Any]] = {} # {trajectory_name: {device_id: trajectory_points}}
        
        # 轨迹文件存储路径
        if trajectory_folder:
            self._trajectory_dir = trajectory_folder
        else:
            self._trajectory_dir = os.path.join(os.path.dirname(__file__), "trajectories")
        os.makedirs(self._trajectory_dir, exist_ok=True)
        
        # 添加重复数据过滤机制
        self._last_recorded_points: Dict[str, Dict[str, float]] = {}  # device_id -> {position, velocity}
        self._min_position_change = 0.01  # 最小位置变化阈值
        self._min_velocity_change = 0.01  # 最小速度变化阈值
        self._min_time_interval = 0.1     # 最小时间间隔（秒）
        self._last_record_time: Dict[str, float] = {}  # device_id -> last_record_time
        
        # 新增：轨迹规划相关 - 在加载轨迹之前初始化
        self._trajectory_planner = RobotTrajectory()  # 轨迹规划器
        self._planned_trajectories: Dict[str, Dict[str, Any]] = {}  # {trajectory_name: planned_data}
        self._playback_timer = QTimer()  # 轨迹播放定时器
        self._playback_timer.timeout.connect(self._play_next_point)
        self._current_playback: Dict[str, Any] = {}  # 当前播放状态
        
        # 加载已保存的轨迹 - 在轨迹规划器初始化之后
        self._load_saved_trajectories()
        
        self.logger.info("TeachingTrajectoryManager: 初始化完成。")

    def _load_saved_trajectories(self):
        """加载已保存的轨迹文件"""
        try:
            for filename in os.listdir(self._trajectory_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(self._trajectory_dir, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        trajectory_data = json.load(f)
                        trajectory_name = filename[:-5]  # 去掉.json后缀
                        self._stored_trajectories[trajectory_name] = trajectory_data
                        # 不再自动规划，改为按需规划
                        self.logger.info(f"TeachingTrajectoryManager: 已加载轨迹 '{trajectory_name}'")
        except Exception as e:
            self.logger.error(f"TeachingTrajectoryManager: 加载轨迹文件失败: {e}")

    def _plan_trajectory(self, trajectory_name: str, keep_original_time: bool = True, uniform_duration: float = 5.0):
        """
        对轨迹进行规划，生成更细的轨迹曲线
        :param trajectory_name: 轨迹名称
        :param keep_original_time: True to use original timestamps, False to use uniform time.
        :param uniform_duration: The total duration for uniform time planning.
        """
        try:
            if trajectory_name not in self._stored_trajectories:
                return
            
            trajectory_data = self._stored_trajectories[trajectory_name]
            points = trajectory_data.get('points', [])
            
            # 过滤出有效的轨迹点（排除开始和结束标记）
            valid_points = [p for p in points if p.get('type') == 'point']
            
            if len(valid_points) < 2:
                self.logger.warning(f"TeachingTrajectoryManager: 轨迹 '{trajectory_name}' 有效点不足，无法规划")
                return
            
            # 提取位置和时间数据
            positions = [p['position'] for p in valid_points]
            
            # 根据选项决定使用哪个时间向量
            if keep_original_time:
                timestamps = [p['timestamp'] for p in valid_points]
                start_time = timestamps[0]
                time_vector = np.array([t - start_time for t in timestamps])
                self.logger.info(f"使用原始时间戳进行轨迹规划, 总时长: {time_vector[-1]:.2f}s")
            else:
                time_vector = np.linspace(0, uniform_duration, len(positions))
                self.logger.info(f"使用统一时间进行轨迹规划, 总时长: {uniform_duration}s")

            if time_vector[-1] < 0.1:
                self.logger.warning(f"轨迹 '{trajectory_name}' 时间过短 ({time_vector[-1]:.2f}s)，无法规划。")
                return
            
            # 生成规划后的轨迹
            planned_t, planned_pos, planned_vel, planned_acc = self._trajectory_planner.generate_waypoint_trajectory(
                positions, time_vector, stop_in_point=False
            )
            # 按需规划时，不再自动弹出绘图窗口
            # self._trajectory_planner.plot_trajectory(planned_t, planned_pos, planned_vel, planned_acc, f"轨迹规划: {trajectory_name}",
            #                                          original_waypoints=positions, original_times=time_vector)
            
            # 存储规划后的轨迹
            planned_data = {
                'original_points': valid_points,
                'original_times': time_vector.tolist(),  # 存储用于规划的时间
                'planned_times': planned_t.tolist(),
                'planned_positions': planned_pos.tolist(),
                'planned_velocities': planned_vel.tolist(),
                'planned_accelerations': planned_acc.tolist(),
                'total_time': time_vector[-1],
                'point_count': len(planned_t)
            }
            
            self._planned_trajectories[trajectory_name] = planned_data
            self.logger.info(f"TeachingTrajectoryManager: 轨迹 '{trajectory_name}' 规划完成，生成 {len(planned_t)} 个点")
            
        except Exception as e:
            self.logger.error(f"TeachingTrajectoryManager: 轨迹规划失败 '{trajectory_name}': {e}")

    def get_planned_trajectory(self, trajectory_name: str) -> Dict[str, Any]:
        """
        获取规划后的轨迹数据。如果轨迹未规划，则进行规划。
        :param trajectory_name: 轨迹名称
        :return: 规划后的轨迹数据
        """
        if trajectory_name not in self._planned_trajectories:
            self.logger.info(f"轨迹 '{trajectory_name}' 尚未规划，现在开始规划...")
            self._plan_trajectory(trajectory_name)  # 使用默认参数进行规划

        return self._planned_trajectories.get(trajectory_name, {})

    def get_trajectory_visualization_data(self, trajectory_name: str) -> Dict[str, Any]:
        """
        获取轨迹可视化数据（原始轨迹和规划后轨迹）
        :param trajectory_name: 轨迹名称
        :return: 可视化数据字典
        """
        if trajectory_name not in self._stored_trajectories:
            return {}
        
        # 确保轨迹已规划
        planned_data = self.get_planned_trajectory(trajectory_name)
        if not planned_data:
            self.logger.error(f"无法获取或生成轨迹 '{trajectory_name}' 的规划数据。")
            return {}
        
        trajectory_data = self._stored_trajectories[trajectory_name]
        
        # 原始轨迹数据（使用相对时间）
        original_points = [p for p in trajectory_data.get('points', []) if p.get('type') == 'point']
        original_times = planned_data.get('original_times', [])  # 使用规划时计算的相对时间
        original_positions = [p['position'] for p in original_points]
        
        # 规划后轨迹数据
        planned_times = planned_data.get('planned_times', [])
        planned_positions = planned_data.get('planned_positions', [])
        
        return {
            'original_times': original_times,
            'original_positions': original_positions,
            'planned_times': planned_times,
            'planned_positions': planned_positions,
            'trajectory_name': trajectory_name,
            'total_time': planned_data.get('total_time', 5.0)  # 返回总时长
        }

    def replan_trajectory_with_duration(self, trajectory_name: str, duration: float):
        """
        使用新的时长重新规划轨迹。
        :param trajectory_name: 轨迹名称。
        :param duration: 新的总执行时长。
        """
        self.logger.info(f"正在以 {duration}秒 的新时长重新规划轨迹: '{trajectory_name}'")
        # 直接调用内部规划函数，并强制使用均匀时间模式
        self._plan_trajectory(
            trajectory_name, 
            keep_original_time=False, 
            uniform_duration=duration
        )

    def replan_trajectory_with_original_time(self, trajectory_name: str):
        """
        使用原始示教时间戳重新规划轨迹。
        :param trajectory_name: 轨迹名称。
        """
        self.logger.info(f"正在以原始时间戳重新规划轨迹: '{trajectory_name}'")
        # 强制使用原始时间模式
        self._plan_trajectory(trajectory_name, keep_original_time=True)

    @Slot(str)
    def start_teaching(self, device_id: str):
        """
        开始示教模式
        :param device_id: 要开始示教的设备ID
        """
        self.logger.info(f"TeachingTrajectoryManager: 开始示教模式 for device '{device_id}'")
        
        # 设置示教标志
        self._teaching_sessions[device_id] = True
        
        # 发送示教状态变化信号
        self._teaching_status_changed.emit(device_id, True)
        
        # 初始化录制会话
        self._recording_sessions[device_id] = []
        
        # 重置过滤状态
        if device_id in self._last_recorded_points:
            del self._last_recorded_points[device_id]
        if device_id in self._last_record_time:
            del self._last_record_time[device_id]
        
        # 记录开始时间
        start_time = time.time()
        self._recording_sessions[device_id].append({
            'timestamp': start_time,
            'type': 'start',
            'message': '示教开始'
        })
        
        self.logger.info(f"TeachingTrajectoryManager: 示教模式已启动 for device '{device_id}'")

    @Slot(str)
    def stop_teaching(self, device_id: str) -> Optional[str]:
        """
        停止示教模式, 并自动保存轨迹。
        :param device_id: 要停止示教的设备ID
        :return: 保存后的轨迹名称，如果失败则返回 None
        """
        self.logger.info(f"TeachingTrajectoryManager: 停止示教模式 for device '{device_id}'")
        
        # 清除示教标志
        if device_id in self._teaching_sessions:
            self._teaching_sessions[device_id] = False
        
        # 发送示教状态变化信号
        self._teaching_status_changed.emit(device_id, False)
        
        # 检查是否有录制会话
        if device_id not in self._recording_sessions or len(self._recording_sessions[device_id]) <= 1:
            self.logger.error(f"TeachingTrajectoryManager: 设备 '{device_id}' 没有录制到有效的轨迹数据点")
            if device_id in self._recording_sessions:
                del self._recording_sessions[device_id]
            return None

        # 记录结束时间
        end_time = time.time()
        self._recording_sessions[device_id].append({
            'timestamp': end_time,
            'type': 'end',
            'message': '示教结束'
        })
        
        # 生成唯一的轨迹名称
        trajectory_name = f"trajectory_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.logger.info(f"TeachingTrajectoryManager: 示教模式已停止 for device '{device_id}', 准备保存为 '{trajectory_name}'")
        
        # 调用保存方法
        if self.save_trajectory(device_id, trajectory_name):
            return trajectory_name
        else:
            # 清理失败的录制会话
            if device_id in self._recording_sessions:
                del self._recording_sessions[device_id]
            return None

    @Slot(str, float, float)
    def record_trajectory_point(self, device_id: str, position: float, velocity: float):
        """
        记录轨迹点（位置和速度）
        :param device_id: 设备ID
        :param position: 位置值
        :param velocity: 速度值
        """
        if not self._teaching_sessions.get(device_id, False):
            return  # 如果不在示教模式，直接返回
        
        current_time = time.time()
        
        # 检查时间间隔
        if device_id in self._last_record_time:
            time_diff = current_time - self._last_record_time[device_id]
            if time_diff < self._min_time_interval:
                return  # 时间间隔太短，跳过记录
        
        # 检查位置和速度变化
        should_record = True
        if device_id in self._last_recorded_points:
            last_point = self._last_recorded_points[device_id]
            position_diff = abs(position - last_point.get('position', 0))
            velocity_diff = abs(velocity - last_point.get('velocity', 0))
            
            # 只有当位置或速度变化超过阈值时才记录
            if position_diff < self._min_position_change and velocity_diff < self._min_velocity_change:
                should_record = False
        
        if not should_record:
            self.logger.debug(f"TeachingTrajectoryManager: 跳过重复轨迹点 for device '{device_id}': pos={position:.2f}, vel={velocity:.2f}")
            return
        
        timestamp = current_time
        point_data = {
            'timestamp': timestamp,
            'type': 'point',
            'position': position,
            'velocity': velocity
        }
        
        if device_id not in self._recording_sessions:
            self._recording_sessions[device_id] = []
        
        self._recording_sessions[device_id].append(point_data)
        
        # 更新最后记录的点和时间
        self._last_recorded_points[device_id] = {'position': position, 'velocity': velocity}
        self._last_record_time[device_id] = current_time
        
        self.logger.debug(f"TeachingTrajectoryManager: 记录轨迹点 for device '{device_id}': pos={position:.2f}, vel={velocity:.2f}")

    @Slot(str, str)
    def save_trajectory(self, device_id: str, trajectory_name: str) -> bool:
        """
        保存示教轨迹到本地文件
        :param device_id: 设备ID
        :param trajectory_name: 轨迹名称
        :return: 是否保存成功
        """
        try:
            if device_id not in self._recording_sessions:
                self.logger.warning(f"TeachingTrajectoryManager: 设备 '{device_id}' 没有录制的轨迹数据")
                return False
            
            trajectory_data = {
                'device_id': device_id,
                'created_time': datetime.now().isoformat(),
                'points': self._recording_sessions[device_id]
            }
            
            # 保存到内存
            self._stored_trajectories[trajectory_name] = trajectory_data
            
            # 保存到文件
            filepath = os.path.join(self._trajectory_dir, f"{trajectory_name}.json")
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(trajectory_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"TeachingTrajectoryManager: 轨迹 '{trajectory_name}' 已保存到 {filepath}")
            
            # 自动规划轨迹
            self._plan_trajectory(trajectory_name)
            
            # 发送轨迹录制完成信号
            self._trajectory_recorded.emit(device_id, trajectory_name, self._recording_sessions[device_id])
            
            return True
            
        except Exception as e:
            self.logger.error(f"TeachingTrajectoryManager: 保存轨迹失败: {e}")
            return False

    @Slot(str)
    def load_trajectory(self, trajectory_name: str) -> Dict[str, Any]:
        """
        加载指定的轨迹
        :param trajectory_name: 轨迹名称
        :return: 轨迹数据字典
        """
        if trajectory_name in self._stored_trajectories:
            self.logger.info(f"TeachingTrajectoryManager: 加载轨迹 '{trajectory_name}'")
            return self._stored_trajectories[trajectory_name]
        else:
            self.logger.warning(f"TeachingTrajectoryManager: 轨迹 '{trajectory_name}' 不存在")
            return {}

    @Slot(str)
    def get_available_trajectories(self) -> List[str]:
        """
        获取所有可用的轨迹名称列表
        :return: 轨迹名称列表
        """
        return list(self._stored_trajectories.keys())

    @Slot(str)
    def delete_trajectory(self, trajectory_name: str) -> bool:
        """
        删除指定的轨迹
        :param trajectory_name: 轨迹名称
        :return: 是否删除成功
        """
        try:
            if trajectory_name in self._stored_trajectories:
                # 从内存中删除
                del self._stored_trajectories[trajectory_name]
                
                # 从文件中删除
                filepath = os.path.join(self._trajectory_dir, f"{trajectory_name}.json")
                if os.path.exists(filepath):
                    os.remove(filepath)
                
                self.logger.info(f"TeachingTrajectoryManager: 轨迹 '{trajectory_name}' 已删除")
                return True
            else:
                self.logger.warning(f"TeachingTrajectoryManager: 轨迹 '{trajectory_name}' 不存在")
                return False
                
        except Exception as e:
            self.logger.error(f"TeachingTrajectoryManager: 删除轨迹失败: {e}")
            return False

    @Slot(str)
    def is_teaching(self, device_id: str) -> bool:
        """
        检查指定设备是否在示教模式
        :param device_id: 设备ID
        :return: 是否在示教模式
        """
        return self._teaching_sessions.get(device_id, False)

    @Slot(str, str)
    def play_trajectory(self, device_id: str, trajectory_name: str):
        """
        播放指定设备的示教轨迹。
        :param device_id: 播放轨迹的设备ID。
        :param trajectory_name: 要播放的轨迹名称。
        """
        self.logger.info(f"TeachingTrajectoryManager: 播放轨迹 '{trajectory_name}' for device '{device_id}'")
        
        if trajectory_name not in self._planned_trajectories:
            self.logger.warning(f"TeachingTrajectoryManager: 轨迹 '{trajectory_name}' 不存在或未规划。")
            self._trajectory_playback_error.emit(device_id, f"轨迹 '{trajectory_name}' 不存在或未规划")
            return

        planned_data = self._planned_trajectories[trajectory_name]
        planned_times = planned_data.get('planned_times', [])
        planned_positions = planned_data.get('planned_positions', [])
        
        if not planned_times or not planned_positions:
            self.logger.warning(f"TeachingTrajectoryManager: 轨迹 '{trajectory_name}' 数据为空。")
            self._trajectory_playback_error.emit(device_id, f"轨迹 '{trajectory_name}' 数据为空")
            return

        # 设置播放状态
        self._current_playback = {
            'device_id': device_id,
            'trajectory_name': trajectory_name,
            'times': planned_times,
            'positions': planned_positions,
            'current_index': 0,
            'start_time': time.time(),
            'total_points': len(planned_times)
        }
        
        # 发送播放开始信号
        self._trajectory_playback_started.emit(device_id, trajectory_name)
        
        # 开始定时器播放
        self._playback_timer.start(50)  # 50ms间隔，约20Hz
        
        self.logger.info(f"TeachingTrajectoryManager: 开始播放轨迹 '{trajectory_name}'，共 {len(planned_times)} 个点")

    def _play_next_point(self):
        """
        播放下一个轨迹点（定时器回调）
        """
        if not self._current_playback:
            self._playback_timer.stop()
            return
        
        playback = self._current_playback
        current_index = playback['current_index']
        times = playback['times']
        positions = playback['positions']
        device_id = playback['device_id']
        trajectory_name = playback['trajectory_name']
        
        if current_index >= len(times):
            # 播放完成
            self._playback_timer.stop()
            self._trajectory_playback_finished.emit(device_id, trajectory_name)
            self._current_playback = {}
            self.logger.info(f"TeachingTrajectoryManager: 轨迹 '{trajectory_name}' 播放完成")
            return
        
        # 获取当前时间点
        current_time = times[current_index]
        current_position = positions[current_index]
        
        # 发送轨迹点就绪信号
        self._trajectory_point_ready.emit(device_id, current_position, 0.0)  # 暂时不考虑速度
        
        # 更新进度
        progress = int((current_index + 1) / len(times) * 100)
        self._playback_progress.emit(device_id, progress)
        
        # 移动到下一个点
        playback['current_index'] = current_index + 1
        
        self.logger.debug(f"TeachingTrajectoryManager: 播放点 {current_index + 1}/{len(times)}, 位置: {current_position:.2f}")

    def stop_playback(self):
        """
        停止轨迹播放
        """
        if self._current_playback:
            device_id = self._current_playback.get('device_id', '')
            trajectory_name = self._current_playback.get('trajectory_name', '')
            
            self._playback_timer.stop()
            self._current_playback = {}
            
            self.logger.info(f"TeachingTrajectoryManager: 停止播放轨迹 '{trajectory_name}'")
            self._trajectory_playback_finished.emit(device_id, trajectory_name)

    @Slot(str)
    def get_trajectory_names_for_device(self, device_id: str) -> List[str]:
        """
        获取指定设备已存储的轨迹名称列表。
        :param device_id: 设备ID。
        :return: 轨迹名称列表。
        """
        return [name for name, data in self._stored_trajectories.items() 
                if data.get('device_id') == device_id]

    def cleanup(self):
        """
        清理示教管理器资源。
        """
        # 停止播放定时器
        if self._playback_timer.isActive():
            self._playback_timer.stop()
        
        self.logger.info("TeachingTrajectoryManager: 清理完成。")