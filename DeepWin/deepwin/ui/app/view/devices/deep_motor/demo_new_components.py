"""
DeepMotor 新组件演示
展示如何使用重构后的组件
"""

import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtCore import QTimer
from qfluentwidgets import setTheme, Theme

# 导入新组件
from .components import (
    UniversalPlotWidget, CommunicationWidget, MotorControlWidget, 
    TeachingControlWidget, HistoryCurveWidget
)
from deepwin.data_management.log_manager import LogManager
from deepwin.config.config_manager import ConfigManager


class DeepMotorDemoWindow(QMainWindow):
    """DeepMotor 组件演示窗口"""
    
    def __init__(self):
        super().__init__()
        
        # 设置主题
        setTheme(Theme.AUTO)
        
        # 初始化日志和配置管理器
        self.log_manager = LogManager()
        self.config_manager = ConfigManager()
        
        self.setWindowTitle("DeepMotor 组件演示")
        self.setGeometry(100, 100, 1400, 900)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 设置布局
        layout = QVBoxLayout(central_widget)
        
        # 创建组件
        self._create_components(layout)
        
        # 连接信号
        self._connect_signals()
        
        # 启动演示定时器
        self._start_demo_timer()
        
    def _create_components(self, layout):
        """创建组件"""
        # 电机控制组件
        self.motor_control = MotorControlWidget("电机控制演示", self.log_manager)
        layout.addWidget(self.motor_control)
        
        # 示教控制组件
        self.teaching_control = TeachingControlWidget("示教控制演示", self.log_manager)
        layout.addWidget(self.teaching_control)
        
        # 通信监控组件
        self.communication = CommunicationWidget("通信监控演示", self.log_manager)
        layout.addWidget(self.communication)
        
        # 历史曲线组件
        self.history_curve = HistoryCurveWidget("历史曲线演示", self.log_manager)
        layout.addWidget(self.history_curve)
        
    def _connect_signals(self):
        """连接信号"""
        # 电机控制信号
        self.motor_control.command_requested.connect(self._on_motor_command)
        self.motor_control.sim_data_requested.connect(self._on_sim_data_request)
        
        # 示教控制信号
        self.teaching_control.start_teaching_requested.connect(self._on_start_teaching)
        self.teaching_control.stop_teaching_requested.connect(self._on_stop_teaching)
        self.teaching_control.execute_teaching_requested.connect(self._on_execute_teaching)
        
        # 通信监控信号
        self.communication.protocol_changed.connect(self._on_protocol_changed)
        
        # 历史曲线信号
        self.history_curve.param_changed.connect(self._on_param_changed)
        
    def _start_demo_timer(self):
        """启动演示定时器"""
        # 模拟数据更新定时器
        self.demo_timer = QTimer()
        self.demo_timer.timeout.connect(self._update_demo_data)
        self.demo_timer.start(1000)  # 每秒更新一次
        
        # 模拟通信数据定时器
        self.comm_timer = QTimer()
        self.comm_timer.timeout.connect(self._update_communication_data)
        self.comm_timer.start(2000)  # 每2秒更新一次
        
    def _update_demo_data(self):
        """更新演示数据"""
        import random
        import time
        
        # 模拟电机状态数据
        motor_status = {
            'position': random.uniform(-180, 180),
            'velocity': random.uniform(-10, 10),
            'torque': random.uniform(-5, 5),
            'temperature': random.uniform(20, 60)
        }
        self.motor_control.update_motor_status(motor_status)
        
        # 模拟历史数据
        current_time = time.time()
        history_data = {
            'data': [
                (current_time - 10, random.uniform(-180, 180)),
                (current_time - 8, random.uniform(-180, 180)),
                (current_time - 6, random.uniform(-180, 180)),
                (current_time - 4, random.uniform(-180, 180)),
                (current_time - 2, random.uniform(-180, 180)),
                (current_time, random.uniform(-180, 180))
            ]
        }
        self.history_curve.update_history_data(history_data)
        
    def _update_communication_data(self):
        """更新通信数据"""
        import random
        
        # 模拟串口数据
        if random.choice([True, False]):
            data = bytes([random.randint(0, 255) for _ in range(8)])
            direction = random.choice(['send', 'receive'])
            description = f"模拟串口数据 - {direction}"
            self.communication.add_serial_data(direction, data, description)
        
        # 模拟CAN数据
        if random.choice([True, False]):
            can_id = random.randint(0x100, 0x7FF)
            data = bytes([random.randint(0, 255) for _ in range(8)])
            direction = random.choice(['send', 'receive'])
            description = f"模拟CAN数据 - {direction}"
            self.communication.add_can_data(direction, can_id, data, description)
            
    def _on_motor_command(self, command: str, params: list):
        """电机命令处理"""
        print(f"电机命令: {command}, 参数: {params}")
        
    def _on_sim_data_request(self):
        """模拟数据请求处理"""
        print("模拟数据请求")
        
    def _on_start_teaching(self, motor_id: int):
        """开始示教处理"""
        print(f"开始示教，电机ID: {motor_id}")
        
    def _on_stop_teaching(self):
        """停止示教处理"""
        print("停止示教")
        
    def _on_execute_teaching(self, trajectory_name: str, use_planned: bool, motor_id: int):
        """执行示教处理"""
        print(f"执行示教，轨迹: {trajectory_name}, 使用规划: {use_planned}, 电机ID: {motor_id}")
        
    def _on_protocol_changed(self, protocol: str):
        """协议改变处理"""
        print(f"通信协议改变: {protocol}")
        
    def _on_param_changed(self, param_name: str):
        """参数改变处理"""
        print(f"历史参数改变: {param_name}")


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 创建演示窗口
    window = DeepMotorDemoWindow()
    window.show()
    
    # 运行应用
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
