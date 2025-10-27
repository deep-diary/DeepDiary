#!/usr/bin/env python3
"""
MQTT协议数据结构生成器
根据 mqtt_protocol.json 自动生成 C++ 头文件
"""

import json
import sys
from pathlib import Path

def cpp_type(json_type):
    """转换JSON类型到C++类型"""
    type_map = {
        "string": "std::string",
        "integer": "int",
        "float": "float",
        "boolean": "bool",
        "object": "cJSON*"
    }
    return type_map.get(json_type, "auto")

def generate_comment(description):
    """生成注释"""
    return f"    // {description}\n"

def generate_struct_fields(schema, indent_level=0):
    """生成结构体字段"""
    indent = "    " * indent_level
    code = ""
    
    if isinstance(schema, dict):
        for key, value in schema.items():
            if isinstance(value, dict):
                if "type" in value:
                    cpp_t = cpp_type(value["type"])
                    desc = value.get("description", "")
                    
                    code += f"{indent}{cpp_t} {key};\n"
                    if desc:
                        code = generate_comment(desc) + code
                elif "fields" in value:
                    # 嵌套对象
                    code += f"{indent}struct {{\n"
                    code += generate_struct_fields(value["fields"], indent_level + 1)
                    code += f"{indent}}} {key};\n"
    
    return code

def generate_protocol_header():
    """生成协议头文件"""
    
    # 读取协议定义
    proto_file = Path(__file__).parent / "mqtt_protocol.json"
    with open(proto_file, 'r', encoding='utf-8') as f:
        protocol = json.load(f)
    
    # 开始生成头文件
    header = '''#ifndef MQTT_PROTOCOL_H
#define MQTT_PROTOCOL_H

/*
 * MQTT协议数据结构定义
 * 此文件由 generate_protocol.py 自动生成
 * 请勿手动修改，如需更改请修改 mqtt_protocol.json
 */

#include <string>
#include <cJSON.h>

#define MQTT_PROTOCOL_VERSION "''' + protocol['version'] + '''"

// 主题定义
'''
    
    # 生成主题相关定义
    topics_code = ""
    for topic_name, topic_def in protocol['topics'].items():
        topic_var = topic_name.upper()
        topic_name_value = topic_def['name']
        
        topics_code += f"#define TOPIC_{topic_var}_PATTERN \"{topic_name_value}\"\n"
        topics_code += f"// 发送周期: {topic_def['period_ms']}ms\n"
        topics_code += f"#define PERIOD_{topic_var} {topic_def['period_ms']}\n\n"
    
    header += topics_code
    
    # 生成设备信息结构体
    device_info_fields = protocol['topics']['device_info']['fields']
    header += "\n// 设备固定配置信息\n"
    header += "struct DeviceInfo {\n"
    
    for key, value in device_info_fields.items():
        if isinstance(value, dict) and "type" in value:
            cpp_t = cpp_type(value["type"])
            desc = value.get("description", "")
            if desc:
                header += f"    // {desc}\n"
            header += f"    {cpp_t} {key};\n"
        elif isinstance(value, dict) and "fields" in value:
            # 嵌套对象
            header += f"    // {value.get('description', '')}\n"
            header += f"    struct {{\n"
            for sub_key, sub_value in value["fields"].items():
                if isinstance(sub_value, dict) and "type" in sub_value:
                    cpp_t = cpp_type(sub_value["type"])
                    desc = sub_value.get("description", "")
                    if desc:
                        header += f"        // {desc}\n"
                    header += f"        {cpp_t} {sub_key};\n"
            header += f"    }} {key};\n"
    
    header += "    \n    DeviceInfo() = default;\n"
    header += "};\n\n"
    
    # 生成设备状态结构体
    device_status = protocol['topics']['device_status']
    header += "// 设备动态状态信息\n"
    header += "struct DeviceStatus {\n"
    
    for category_name, category_def in device_status['categories'].items():
        header += f"    \n    // {category_def['description']}\n"
        header += f"    struct {{\n"
        
        for key, value in category_def['fields'].items():
            if isinstance(value, dict):
                if "type" in value:
                    cpp_t = cpp_type(value["type"])
                    desc = value.get("description", "")
                    if desc:
                        header += f"        // {desc}\n"
                    header += f"        {cpp_t} {key};\n"
                elif "fields" in value:
                    # 嵌套对象
                    header += f"        struct {{\n"
                    for sub_key, sub_value in value["fields"].items():
                        if isinstance(sub_value, dict) and "type" in sub_value:
                            cpp_t = cpp_type(sub_value["type"])
                            desc = sub_value.get("description", "")
                            if desc:
                                header += f"            // {desc}\n"
                            header += f"            {cpp_t} {sub_key};\n"
                    header += f"        }} {key};\n"
        
        header += f"    }} {category_name};\n"
    
    header += "    \n    DeviceStatus() = default;\n"
    header += "};\n\n"
    
    # 生成事件结构体
    device_events = protocol['topics']['device_events']['fields']
    header += "// 设备事件消息\n"
    header += "struct DeviceEvent {\n"
    
    for key, value in device_events.items():
        if isinstance(value, dict) and "type" in value:
            cpp_t = cpp_type(value["type"])
            desc = value.get("description", "")
            if desc:
                header += f"    // {desc}\n"
            header += f"    {cpp_t} {key};\n"
    
    header += "    \n    DeviceEvent() = default;\n"
    header += "};\n\n"
    
    header += "#endif // MQTT_PROTOCOL_H\n"
    
    return header

def main():
    """主函数"""
    try:
        output_file = Path(__file__).parent / "mqtt_protocol_generated.h"
        header_content = generate_protocol_header()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(header_content)
        
        print(f"✅ 已生成协议头文件: {output_file}")
        return 0
        
    except Exception as e:
        print(f"❌ 生成失败: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())

