#include "device_info_collector.h"
#include "wifi_station.h"
#include "esp_system.h"
#include "esp_mac.h"
#include "esp_chip_info.h"
#include "esp_flash.h"
#include "esp_log.h"
#include "esp_timer.h"
#include <sstream>
#include <iomanip>

#define TAG_DEVICE_INFO "DeviceInfo"

DeviceInfoCollector::DeviceInfoCollector() 
    : deep_motor_(nullptr), deep_arm_(nullptr), gimbal_(nullptr), 
      led_strip_(nullptr), camera_(nullptr), device_id_cached_(false) {
    ESP_LOGI(TAG_DEVICE_INFO, "DeviceInfoCollector initialized");
}

DeviceInfoCollector::~DeviceInfoCollector() {
    ESP_LOGI(TAG_DEVICE_INFO, "DeviceInfoCollector destroyed");
}

void DeviceInfoCollector::SetDeepMotor(DeepMotor* motor) {
    deep_motor_ = motor;
}

void DeviceInfoCollector::SetDeepArm(DeepArm* arm) {
    deep_arm_ = arm;
}

void DeviceInfoCollector::SetGimbal(Gimbal_t* gimbal) {
    gimbal_ = gimbal;
}

void DeviceInfoCollector::SetLedStrip(CircularStrip* led_strip) {
    led_strip_ = led_strip;
}

void DeviceInfoCollector::SetCamera(Esp32Camera* camera) {
    camera_ = camera;
}

DeviceInfo DeviceInfoCollector::CollectDeviceInfo() {
    DeviceInfo info;
    
    // 基本信息
    info.device_id = GetDeviceId();
    info.firmware_version = GetFirmwareVersion();
    info.wifi_ssid = GetWifiInfo();
    info.ip_address = GetIpAddress();
    info.free_heap = GetFreeHeap();
    info.uptime_seconds = GetUptimeSeconds();
    info.cpu_temperature = GetCpuTemperature();
    
    // 组件可用性
    info.camera_available = (camera_ != nullptr);
    info.can_bus_available = true; // CAN总线在板级初始化中已配置
    info.led_strip_available = (led_strip_ != nullptr);
    info.gimbal_available = (gimbal_ != nullptr);
    
    // 机械臂状态
    info.arm_connected = (deep_arm_ != nullptr);
    info.arm_motor_count = info.arm_connected ? 6 : 0; // 假设6个电机
    info.arm_status = GetArmStatus();
    
    // 电机状态
    info.motor_connected = (deep_motor_ != nullptr);
    info.motor_count = info.motor_connected ? 6 : 0; // 假设6个电机
    info.motor_status = GetMotorStatus();
    
    ESP_LOGI(TAG_DEVICE_INFO, "Device info collected - ID: %s, Heap: %d, Uptime: %d", 
             info.device_id.c_str(), info.free_heap, info.uptime_seconds);
    
    return info;
}

std::string DeviceInfoCollector::GetArmStatus() const {
    if (!deep_arm_) {
        return "not_available";
    }
    
    // 这里可以根据实际的DeepArm API来获取状态
    // 暂时返回基本状态
    return "connected";
}

std::string DeviceInfoCollector::GetMotorStatus() const {
    if (!deep_motor_) {
        return "not_available";
    }
    
    // 这里可以根据实际的DeepMotor API来获取状态
    // 暂时返回基本状态
    return "connected";
}

std::string DeviceInfoCollector::GetGimbalStatus() const {
    if (!gimbal_) {
        return "not_available";
    }
    
    // 这里可以根据实际的Gimbal API来获取状态
    // 暂时返回基本状态
    return "connected";
}

std::string DeviceInfoCollector::GetLedStripStatus() const {
    if (!led_strip_) {
        return "not_available";
    }
    
    // 这里可以根据实际的CircularStrip API来获取状态
    // 暂时返回基本状态
    return "connected";
}

std::string DeviceInfoCollector::GetCameraStatus() const {
    if (!camera_) {
        return "not_available";
    }
    
    // 这里可以根据实际的Esp32Camera API来获取状态
    // 暂时返回基本状态
    return "connected";
}

std::string DeviceInfoCollector::GetDeviceId() const {
    if (!device_id_cached_) {
        cached_device_id_ = GenerateDeviceId();
        device_id_cached_ = true;
    }
    return cached_device_id_;
}

std::string DeviceInfoCollector::GetFirmwareVersion() const {
    // 这里可以从版本文件或编译时定义中获取
    return "1.0.0";
}

std::string DeviceInfoCollector::GetWifiInfo() const {
    auto& wifi_station = WifiStation::GetInstance();
    return wifi_station.GetSsid();
}

std::string DeviceInfoCollector::GetIpAddress() const {
    auto& wifi_station = WifiStation::GetInstance();
    return wifi_station.GetWebServerUrl(); // 这里可能需要修改为获取IP地址的方法
}

int DeviceInfoCollector::GetFreeHeap() const {
    return esp_get_free_heap_size();
}

int DeviceInfoCollector::GetUptimeSeconds() const {
    return esp_timer_get_time() / 1000000; // 转换为秒
}

float DeviceInfoCollector::GetCpuTemperature() const {
    // ESP32-S3没有内置温度传感器，返回0
    return 0.0f;
}

std::string DeviceInfoCollector::GenerateDeviceId() const {
    std::string mac = GetMacAddress();
    std::string chip_model = GetChipModel();
    
    // 使用MAC地址和芯片型号生成设备ID
    std::stringstream ss;
    ss << "ATK-DNESP32S3-" << chip_model << "-" << mac.substr(0, 8);
    return ss.str();
}

std::string DeviceInfoCollector::GetMacAddress() const {
    uint8_t mac[6];
    esp_read_mac(mac, ESP_MAC_WIFI_STA);
    
    std::stringstream ss;
    for (int i = 0; i < 6; i++) {
        ss << std::hex << std::setfill('0') << std::setw(2) << (int)mac[i];
        if (i < 5) ss << ":";
    }
    return ss.str();
}

std::string DeviceInfoCollector::GetChipModel() const {
    esp_chip_info_t chip_info;
    esp_chip_info(&chip_info);
    
    switch (chip_info.model) {
        case CHIP_ESP32: return "ESP32";
        case CHIP_ESP32S2: return "ESP32-S2";
        case CHIP_ESP32S3: return "ESP32-S3";
        case CHIP_ESP32C3: return "ESP32-C3";
        case CHIP_ESP32C6: return "ESP32-C6";
        case CHIP_ESP32H2: return "ESP32-H2";
        default: return "Unknown";
    }
}

std::string DeviceInfoCollector::GetChipRevision() const {
    esp_chip_info_t chip_info;
    esp_chip_info(&chip_info);
    
    std::stringstream ss;
    ss << chip_info.revision;
    return ss.str();
}

std::string DeviceInfoCollector::GetChipFeatures() const {
    esp_chip_info_t chip_info;
    esp_chip_info(&chip_info);
    
    std::stringstream ss;
    if (chip_info.features & CHIP_FEATURE_WIFI_BGN) ss << "WiFi ";
    if (chip_info.features & CHIP_FEATURE_BT) ss << "BT ";
    if (chip_info.features & CHIP_FEATURE_BLE) ss << "BLE ";
    if (chip_info.features & CHIP_FEATURE_IEEE802154) ss << "802.15.4 ";
    if (chip_info.features & CHIP_FEATURE_EMB_FLASH) ss << "Embedded-Flash ";
    if (chip_info.features & CHIP_FEATURE_EXTERNAL_FLASH) ss << "External-Flash ";
    
    return ss.str();
}

std::string DeviceInfoCollector::GetFlashInfo() const {
    uint32_t flash_size;
    esp_flash_get_size(nullptr, &flash_size);
    
    std::stringstream ss;
    ss << flash_size / (1024 * 1024) << "MB";
    return ss.str();
}

std::string DeviceInfoCollector::GetPsramInfo() const {
    size_t psram_size = esp_psram_get_size();
    
    std::stringstream ss;
    if (psram_size > 0) {
        ss << psram_size / (1024 * 1024) << "MB";
    } else {
        ss << "Not available";
    }
    return ss.str();
}

