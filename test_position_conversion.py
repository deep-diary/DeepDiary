#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试位置转换逻辑的脚本
"""

import struct

def test_position_conversion():
    """测试位置转换逻辑"""
    
    # 模拟_decode_can_data中的解码逻辑
    def decode_position(data_bytes):
        """解码位置数据"""
        POSITION_RANGE = (-4 * 3.14159, 4 * 3.14159)  # -4π ~ 4π
        
        # Parse position data (Byte 0-1)
        position_raw = struct.unpack('>H', data_bytes[0:2])[0]
        position_raw = position_raw - 32767
        position = scale_value(position_raw, -32768, 32767, POSITION_RANGE[0], POSITION_RANGE[1])
        return position
    
    def scale_value(value, in_min, in_max, out_min, out_max):
        """缩放值"""
        return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
    
    # 模拟sim_read_serial_data中的编码逻辑
    def encode_position(position):
        """编码位置数据"""
        POSITION_RANGE = (-4 * 3.14159, 4 * 3.14159)  # -4π ~ 4π
        
        # 1. 首先将位置限制在POSITION_RANGE范围内
        position = min(max(position, POSITION_RANGE[0]), POSITION_RANGE[1])
        
        # 2. 使用_scale_value的逆运算，将位置映射到-32768到32767范围
        position_raw = (position - POSITION_RANGE[0]) * (32767 - (-32768)) / (POSITION_RANGE[1] - POSITION_RANGE[0]) + (-32768)
        position_raw = int(position_raw)
        
        # 3. 确保position_raw在有效范围内
        position_raw = max(-32768, min(32767, position_raw))
        
        # 4. 加上32767得到无符号值
        position_uint = position_raw + 32767
        
        # 5. 确保无符号值在有效范围内
        position_uint = max(0, min(65535, position_uint))
        
        # 6. 转换为字节（大端序）
        data_bytes = struct.pack('>H', position_uint)
        return data_bytes
    
    # 测试用例
    test_positions = [0.0, 1.0, -1.0, 12.48, -12.48, 4*3.14159, -4*3.14159]
    
    print("位置转换测试:")
    print("=" * 60)
    
    for original_position in test_positions:
        try:
            # 编码
            encoded_bytes = encode_position(original_position)
            
            # 解码
            decoded_position = decode_position(encoded_bytes)
            
            # 计算误差
            error = abs(original_position - decoded_position)
            
            print(f"原始位置: {original_position:8.4f} -> 编码: {encoded_bytes.hex()} -> 解码: {decoded_position:8.4f} (误差: {error:.6f})")
        except Exception as e:
            print(f"原始位置: {original_position:8.4f} -> 错误: {e}")
    
    print("=" * 60)
    print("测试完成!")

if __name__ == "__main__":
    test_position_conversion() 