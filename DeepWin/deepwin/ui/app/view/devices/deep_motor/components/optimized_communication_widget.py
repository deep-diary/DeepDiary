"""
优化版通信显示组件
减少频繁更新，提升性能
"""

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QTextEdit, QPushButton, QComboBox, QGroupBox,
                               QSplitter, QScrollArea, QFrame)
from PySide6.QtGui import QFont
from qfluentwidgets import (PrimaryPushButton, ComboBox, SwitchButton, 
                           CardWidget, TextEdit, ScrollArea)
from datetime import datetime
import json
from typing import Dict, List, Any, Optional
from deepwin.data_management.log_manager import LogManager
from deepwin.config.config_manager import ConfigManager


class OptimizedCommunicationWidget(QWidget):
    """优化版通信显示组件"""
    
    # 信号定义
    protocol_changed = Signal(str)  # 协议切换信号 (serial/can)
    clear_requested = Signal()  # 清空显示请求信号
    
    def __init__(self, title: str = "通信监控", log_manager: LogManager = None, 
                 config_manager: ConfigManager = None, parent=None):
        super().__init__(parent)
        self.logger = log_manager
        self.config_manager = config_manager
        self.title = title
        
        # 通信数据缓存
        self.serial_data = []  # 串口数据
        self.can_data = []     # CAN数据
        self.max_display_items = 500  # 减少最大显示条目数
        
        # 当前显示的协议类型
        self.current_protocol = "serial"  # serial 或 can
        
        # 性能优化：使用定时器批量更新显示
        self.update_timer = QTimer(self)
        self.update_timer.setInterval(1000)  # 1秒更新一次显示
        self.update_timer.timeout.connect(self._batch_update_display)
        self._needs_update = False
        
        self.setup_ui()
        
    def setup_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # 创建卡片容器
        self.card = CardWidget(parent=self)
        self.card.setObjectName(self.title)
        card_layout = QVBoxLayout(self.card)
        
        # 标题
        title_label = QLabel(self.title)
        title_label.setObjectName('cardTitle')
        card_layout.addWidget(title_label)
        
        # 通信控制面板
        control_layout = QHBoxLayout()
        
        # 协议选择
        protocol_label = QLabel('通信协议:')
        self.protocol_combo = ComboBox()
        self.protocol_combo.addItems(['串口通信', 'CAN通信'])
        self.protocol_combo.setCurrentText('串口通信')
        
        # 清空按钮
        self.clear_button = PrimaryPushButton('清空显示')
        
        # 自动滚动开关
        auto_scroll_label = QLabel('自动滚动:')
        self.auto_scroll_switch = SwitchButton('开启')
        self.auto_scroll_switch.setChecked(True)
        
        # 统计信息标签
        self.stats_label = QLabel('统计: 发送 0 | 接收 0')
        
        control_layout.addWidget(protocol_label)
        control_layout.addWidget(self.protocol_combo)
        control_layout.addWidget(self.clear_button)
        control_layout.addWidget(auto_scroll_label)
        control_layout.addWidget(self.auto_scroll_switch)
        control_layout.addWidget(self.stats_label)
        control_layout.addStretch()
        
        card_layout.addLayout(control_layout)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 发送数据显示区域
        self.send_widget = self._create_data_display_widget("发送数据", "send")
        
        # 接收数据显示区域
        self.receive_widget = self._create_data_display_widget("接收数据", "receive")
        
        splitter.addWidget(self.send_widget)
        splitter.addWidget(self.receive_widget)
        splitter.setSizes([400, 400])  # 设置初始大小
        
        card_layout.addWidget(splitter)
        
        layout.addWidget(self.card)
        
        # 连接信号
        self.protocol_combo.currentTextChanged.connect(self._on_protocol_changed)
        self.clear_button.clicked.connect(self._on_clear_clicked)
        
    def _create_data_display_widget(self, title: str, data_type: str) -> QWidget:
        """创建数据显示组件"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 标题
        title_label = QLabel(title)
        title_label.setObjectName('subTitle')
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 创建滚动区域
        scroll_area = ScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(200)  # 减小最小高度
        scroll_area.setMaximumHeight(300)  # 减小最大高度
        
        # 文本显示区域
        text_edit = TextEdit()
        text_edit.setReadOnly(True)
        # 设置等宽字体
        font = QFont("Consolas", 8)  # 减小字体大小
        font.setStyleHint(QFont.Monospace)
        text_edit.setFont(font)
        text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 10px;
            }
        """)
        
        scroll_area.setWidget(text_edit)
        layout.addWidget(scroll_area)
        
        # 保存引用
        if data_type == "send":
            self.send_text_edit = text_edit
            self.send_scroll_area = scroll_area
        else:
            self.receive_text_edit = text_edit
            self.receive_scroll_area = scroll_area
            
        return widget
        
    def _on_protocol_changed(self, protocol_text: str):
        """协议切换处理"""
        if protocol_text == "串口通信":
            self.current_protocol = "serial"
        else:
            self.current_protocol = "can"
            
        if self.logger:
            self.logger.info(f"通信协议切换到: {self.current_protocol}")
            
        # 发射信号
        self.protocol_changed.emit(self.current_protocol)
        
        # 立即更新显示
        self._update_display()
        
    def _on_clear_clicked(self):
        """清空按钮点击处理"""
        if self.logger:
            self.logger.info("清空通信显示")
            
        # 清空数据缓存
        if self.current_protocol == "serial":
            self.serial_data = []
        else:
            self.can_data = []
            
        # 清空显示
        self._update_display()
        
        # 发射信号
        self.clear_requested.emit()
        
    def add_serial_data(self, direction: str, data: bytes, description: str = ""):
        """
        添加串口数据 - 优化版本
        :param direction: 方向 ('send' 或 'receive')
        :param data: 数据字节
        :param description: 描述信息
        """
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]  # 精确到毫秒
        
        # 格式化数据
        if isinstance(data, bytes):
            hex_data = data.hex().upper()
            ascii_data = ''.join([chr(b) if 32 <= b <= 126 else '.' for b in data])
        else:
            hex_data = str(data)
            ascii_data = str(data)
            
        data_item = {
            'timestamp': timestamp,
            'direction': direction,
            'hex_data': hex_data,
            'ascii_data': ascii_data,
            'description': description,
            'raw_data': data
        }
        
        self.serial_data.append(data_item)
        
        # 限制数据量
        if len(self.serial_data) > self.max_display_items:
            self.serial_data = self.serial_data[-self.max_display_items:]
            
        # 标记需要更新，但不立即更新
        self._needs_update = True
        if not self.update_timer.isActive():
            self.update_timer.start()
            
        if self.logger:
            self.logger.debug(f"添加串口数据: {direction} - {description}")
            
    def add_can_data(self, direction: str, can_id: int, data: bytes, description: str = ""):
        """
        添加CAN数据 - 优化版本
        :param direction: 方向 ('send' 或 'receive')
        :param can_id: CAN ID
        :param data: 数据字节
        :param description: 描述信息
        """
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]  # 精确到毫秒
        
        # 格式化数据
        if isinstance(data, bytes):
            hex_data = data.hex().upper()
        else:
            hex_data = str(data)
            
        data_item = {
            'timestamp': timestamp,
            'direction': direction,
            'can_id': can_id,
            'hex_data': hex_data,
            'description': description,
            'raw_data': data
        }
        
        self.can_data.append(data_item)
        
        # 限制数据量
        if len(self.can_data) > self.max_display_items:
            self.can_data = self.can_data[-self.max_display_items:]
            
        # 标记需要更新，但不立即更新
        self._needs_update = True
        if not self.update_timer.isActive():
            self.update_timer.start()
            
        if self.logger:
            self.logger.debug(f"添加CAN数据: {direction} - ID:{can_id:03X} - {description}")
            
    def _batch_update_display(self):
        """批量更新显示"""
        if not self._needs_update:
            return
            
        self._needs_update = False
        self._update_display()
        
    def _update_display(self):
        """更新显示内容"""
        if self.current_protocol == "serial":
            self._update_serial_display()
        else:
            self._update_can_display()
            
        # 更新统计信息
        self._update_statistics()
        
    def _update_serial_display(self):
        """更新串口数据显示"""
        # 分离发送和接收数据
        send_data = [item for item in self.serial_data if item['direction'] == 'send']
        receive_data = [item for item in self.serial_data if item['direction'] == 'receive']
        
        # 更新发送显示
        self._update_text_display(self.send_text_edit, send_data, "serial")
        
        # 更新接收显示
        self._update_text_display(self.receive_text_edit, receive_data, "serial")
        
    def _update_can_display(self):
        """更新CAN数据显示"""
        # 分离发送和接收数据
        send_data = [item for item in self.can_data if item['direction'] == 'send']
        receive_data = [item for item in self.can_data if item['direction'] == 'receive']
        
        # 更新发送显示
        self._update_text_display(self.send_text_edit, send_data, "can")
        
        # 更新接收显示
        self._update_text_display(self.receive_text_edit, receive_data, "can")
        
    def _update_text_display(self, text_edit: TextEdit, data_list: List[Dict], protocol: str):
        """更新文本显示 - 优化版本"""
        if not data_list:
            text_edit.clear()
            return
            
        # 构建显示文本 - 简化版本
        display_text = ""
        for item in data_list[-50:]:  # 只显示最后50条数据
            timestamp = item['timestamp']
            description = item['description']
            
            if protocol == "serial":
                hex_data = item['hex_data']
                ascii_data = item['ascii_data']
                display_text += f"[{timestamp}] {description}\n"
                display_text += f"HEX: {hex_data}\n"
                display_text += f"ASCII: {ascii_data}\n"
                display_text += "-" * 30 + "\n"
            else:  # CAN
                can_id = item['can_id']
                hex_data = item['hex_data']
                display_text += f"[{timestamp}] {description}\n"
                display_text += f"ID: {can_id:03X} | Data: {hex_data}\n"
                display_text += "-" * 30 + "\n"
                
        # 更新显示
        text_edit.setPlainText(display_text)
        
        # 自动滚动到底部
        if self.auto_scroll_switch.isChecked():
            # 使用ensureCursorVisible确保最新内容可见
            text_edit.ensureCursorVisible()
            # 滚动到最底部
            scrollbar = text_edit.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
            
    def _update_statistics(self):
        """更新统计信息"""
        if self.current_protocol == "serial":
            send_count = len([item for item in self.serial_data if item['direction'] == 'send'])
            receive_count = len([item for item in self.serial_data if item['direction'] == 'receive'])
        else:
            send_count = len([item for item in self.can_data if item['direction'] == 'send'])
            receive_count = len([item for item in self.can_data if item['direction'] == 'receive'])
            
        self.stats_label.setText(f"统计: 发送 {send_count} | 接收 {receive_count}")
        
    def get_current_protocol(self) -> str:
        """获取当前协议类型"""
        return self.current_protocol
        
    def set_max_display_items(self, max_items: int):
        """设置最大显示条目数"""
        self.max_display_items = max_items
        
    def export_data(self, file_path: str):
        """导出数据到文件"""
        try:
            export_data = {
                'protocol': self.current_protocol,
                'timestamp': datetime.now().isoformat(),
                'serial_data': self.serial_data,
                'can_data': self.can_data
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
                
            if self.logger:
                self.logger.info(f"通信数据已导出到: {file_path}")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"导出通信数据失败: {e}")
                
    def clear_all_data(self):
        """清空所有数据"""
        self.serial_data = []
        self.can_data = []
        self._needs_update = False
        self.update_timer.stop()
        self._update_display()
        
        if self.logger:
            self.logger.info("已清空所有通信数据")
            
    def add_communication_data(self, direction: str, protocol: str, data: bytes, 
                              description: str = "", can_id: int = None):
        """添加通信数据到显示"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]  # 毫秒级时间戳
        
        # 生成十六进制和ASCII显示
        hex_data = data.hex().upper()
        try:
            ascii_data = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in data)
        except:
            ascii_data = "."
            
        data_item = {
            'timestamp': timestamp,
            'direction': direction,
            'description': description,
            'hex_data': hex_data,
            'ascii_data': ascii_data
        }
        
        if protocol == "serial":
            self.serial_data.append(data_item)
            # 限制最大条目数
            if len(self.serial_data) > self.max_display_items:
                self.serial_data = self.serial_data[-self.max_display_items:]
        else:  # CAN
            data_item['can_id'] = can_id or 0
            self.can_data.append(data_item)
            # 限制最大条目数
            if len(self.can_data) > self.max_display_items:
                self.can_data = self.can_data[-self.max_display_items:]
                
        # 标记需要更新
        self._needs_update = True
        if not self.update_timer.isActive():
            self.update_timer.start()
        
        if self.logger:
            self.logger.debug(f"添加通信数据: {direction} {protocol} - {description}")
