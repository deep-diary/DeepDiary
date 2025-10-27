#ifndef MQTT_PROTOCOL_H
#define MQTT_PROTOCOL_H

/*
 * MQTT协议数据结构定义
 * 此文件由 generate_protocol.py 自动生成
 * 请勿手动修改，如需更改请修改 mqtt_protocol.json
 */

#include <string>
#include <cJSON.h>

#define MQTT_PROTOCOL_VERSION "1.0.0"

// 主题定义
#define TOPIC_DEVICE_INFO_PATTERN "device/{client_id}/info"
// 发送周期: 60000ms
#define PERIOD_DEVICE_INFO 60000

#define TOPIC_DEVICE_STATUS_PATTERN "device/{client_id}/status"
// 发送周期: 10000ms
#define PERIOD_DEVICE_STATUS 10000

#define TOPIC_DEVICE_EVENTS_PATTERN "device/{client_id}/events"
// 发送周期: 0ms
#define PERIOD_DEVICE_EVENTS 0

#define TOPIC_CONTROL_PATTERN "device/{client_id}/control"
// 发送周期: 0ms
#define PERIOD_CONTROL 0


// 设备固定配置信息
struct DeviceInfo {
    // 设备唯一ID
    std::string device_id;
    // 设备类型
    std::string device_type;
    // 固件版本
    std::string firmware_version;
    // MAC地址
    std::string mac_address;
    // 芯片型号
    std::string chip_model;
    // 芯片版本
    std::string chip_revision;
    // 硬件能力
    cJSON* hardware_capabilities;
    
    DeviceInfo() = default;
};

// 设备动态状态信息
struct DeviceStatus {
    
    // 系统动态信息
    struct {
        // WiFi名称
        std::string wifi_ssid;
        // IP地址
        std::string ip_address;
        // 可用堆内存(字节)
        int free_heap;
        // 运行时间(秒)
        int uptime_seconds;
        // CPU温度
        float cpu_temperature;
        // 网络状态
        std::string network_status;
    } system;
    
    // 传感器数据
    struct {
        // X轴加速度(m/s²)
        float acc_x;
        // Y轴加速度(m/s²)
        float acc_y;
        // Z轴加速度(m/s²)
        float acc_z;
        // 总加速度(m/s²)
        float acc_g;
        // 俯仰角(度)
        float pitch;
        // 翻滚角(度)
        float roll;
        // 传感器状态
        std::string sensor_status;
    } sensor;
    
    // 执行器状态
    struct {
        cJSON* arm;
        cJSON* motor;
    } actuator;
    
    DeviceStatus() = default;
};

// 设备事件消息
struct DeviceEvent {
    // 事件类型
    std::string event_type;
    // 事件消息
    std::string event_message;
    // 时间戳
    int timestamp;
    
    DeviceEvent() = default;
};

#endif // MQTT_PROTOCOL_H
