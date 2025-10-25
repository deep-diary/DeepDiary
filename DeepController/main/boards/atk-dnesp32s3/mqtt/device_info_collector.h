#ifndef DEVICE_INFO_COLLECTOR_H
#define DEVICE_INFO_COLLECTOR_H

#include "user_mqtt_client.h"
#include "deep_motor.h"
#include "deep_arm.h"
#include "Gimbal.h"
#include "CircularStrip.h"
#include "esp32_camera.h"
#include <string>
#include <memory>

class DeviceInfoCollector {
public:
    DeviceInfoCollector();
    ~DeviceInfoCollector();
    
    // 设置设备组件引用
    void SetDeepMotor(DeepMotor* motor);
    void SetDeepArm(DeepArm* arm);
    void SetGimbal(Gimbal_t* gimbal);
    void SetLedStrip(CircularStrip* led_strip);
    void SetCamera(Esp32Camera* camera);
    
    // 收集设备信息
    DeviceInfo CollectDeviceInfo();
    
    // 获取特定组件状态
    std::string GetArmStatus() const;
    std::string GetMotorStatus() const;
    std::string GetGimbalStatus() const;
    std::string GetLedStripStatus() const;
    std::string GetCameraStatus() const;
    
    // 获取系统信息
    std::string GetDeviceId() const;
    std::string GetFirmwareVersion() const;
    std::string GetWifiInfo() const;
    std::string GetIpAddress() const;
    int GetFreeHeap() const;
    int GetUptimeSeconds() const;
    float GetCpuTemperature() const;
    
private:
    DeepMotor* deep_motor_;
    DeepArm* deep_arm_;
    Gimbal_t* gimbal_;
    CircularStrip* led_strip_;
    Esp32Camera* camera_;
    
    // 缓存设备ID
    mutable std::string cached_device_id_;
    mutable bool device_id_cached_;
    
    // 内部方法
    std::string GenerateDeviceId() const;
    std::string GetMacAddress() const;
    std::string GetChipModel() const;
    std::string GetChipRevision() const;
    std::string GetChipFeatures() const;
    std::string GetFlashInfo() const;
    std::string GetPsramInfo() const;
};

#endif // DEVICE_INFO_COLLECTOR_H

