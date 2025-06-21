import time

class TeachingTrajectoryManager:
    def __init__(self, min_time_interval, min_position_change, min_velocity_change):
        self._teaching_sessions = {}
        self._last_record_time = {}
        self._last_recorded_points = {}
        self._recording_sessions = {}
        self._min_time_interval = min_time_interval
        self._min_position_change = min_position_change
        self._min_velocity_change = min_velocity_change
        self.logger = None  # Assuming a logger is set up

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
        if device_id in self._last_record_time:
            time_diff = current_time - self._last_record_time[device_id]
            if time_diff < self._min_time_interval:
                return  # 时间间隔太短，跳过记录
        should_record = True
        if device_id in self._last_recorded_points:
            last_point = self._last_recorded_points[device_id]
            position_diff = abs(position - last_point.get('position', 0))
            velocity_diff = abs(velocity - last_point.get('velocity', 0))
            if position_diff < self._min_position_change and velocity_diff < self._min_velocity_change:
                should_record = False
        if not should_record:
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
        self._last_recorded_points[device_id] = {'position': position, 'velocity': velocity}
        self._last_record_time[device_id] = current_time
        self.logger.info(f"TeachingTrajectoryManager: 记录轨迹点 for device '{device_id}': pos={position:.2f}, vel={velocity:.2f}") 