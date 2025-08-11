from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QGridLayout, QLabel
from qfluentwidgets import SpinBox, PrimaryPushButton

class JointControlWidget(QWidget):
    """关节控制小部件 - 包含6个关节的角度控制"""
    
    # 信号定义
    joint_control_requested = Signal(int, float)  # 关节控制信号 (关节ID, 角度)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 初始化关节控制组件
        self.joint_spinboxes = {}
        self.joint_labels = {}
        
        self.setup_ui()
        self.setup_signals()

    def setup_ui(self):
        """初始化关节控制界面"""
        # 创建网格布局用于关节控制
        joint_grid = QGridLayout(self)
        joint_grid.setSpacing(10)
        
        # 创建6个关节的控制组件
        for i in range(1, 7):
            # 关节标签
            joint_label = QLabel(f'关节 {i}:')
            joint_label.setMinimumWidth(60)
            
            # 关节角度输入框
            joint_spin = SpinBox()
            joint_spin.setRange(-180, 180)  # 关节角度范围
            joint_spin.setSuffix("°")
            joint_spin.setValue(0)
            joint_spin.setMinimumWidth(100)
            
            # 设置关节按钮
            set_joint_button = PrimaryPushButton(f'设置关节{i}')
            set_joint_button.setMinimumWidth(80)
            
            # 存储组件引用
            self.joint_labels[i] = joint_label
            self.joint_spinboxes[i] = joint_spin
            
            # 添加到网格布局
            row = (i - 1) // 3  # 每行3个关节
            col = (i - 1) % 3 * 3  # 每个关节占3列
            joint_grid.addWidget(joint_label, row, col)
            joint_grid.addWidget(joint_spin, row, col + 1)
            joint_grid.addWidget(set_joint_button, row, col + 2)
            
            # 连接信号
            set_joint_button.clicked.connect(
                lambda checked, joint_id=i: self._on_set_joint_clicked(joint_id)
            )

    def setup_signals(self):
        """设置信号连接"""
        pass  # 信号已在setup_ui中连接

    def _on_set_joint_clicked(self, joint_id: int):
        """设置关节按钮点击处理"""
        angle = self.joint_spinboxes[joint_id].value()
        self.joint_control_requested.emit(joint_id, angle)

    # ==================== 公共接口方法 ====================
    
    def update_joint_angle(self, joint_id: int, angle: float):
        """更新关节角度显示"""
        if joint_id in self.joint_spinboxes:
            self.joint_spinboxes[joint_id].setValue(angle)
    
    def get_joint_angle(self, joint_id: int) -> float:
        """获取关节角度值"""
        if joint_id in self.joint_spinboxes:
            return self.joint_spinboxes[joint_id].value()
        return 0.0
    
    def reset_all_joints(self):
        """重置所有关节角度为0"""
        for joint_id in range(1, 7):
            self.joint_spinboxes[joint_id].setValue(0)
    
    def set_joint_enabled(self, joint_id: int, enabled: bool):
        """设置关节是否可用"""
        if joint_id in self.joint_spinboxes:
            self.joint_spinboxes[joint_id].setEnabled(enabled)
            self.joint_labels[joint_id].setEnabled(enabled) 