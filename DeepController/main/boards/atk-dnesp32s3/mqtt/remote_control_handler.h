#ifndef REMOTE_CONTROL_HANDLER_H
#define REMOTE_CONTROL_HANDLER_H

#include "user_mqtt_client.h"
#include "deep_motor.h"
#include "deep_arm.h"
#include "Gimbal.h"
#include "CircularStrip.h"
#include "esp32_camera.h"
#include <string>
#include <memory>
#include <functional>

class RemoteControlHandler {
public:
    RemoteControlHandler();
    ~RemoteControlHandler();
    
    // 设置设备组件引用
    void SetDeepMotor(DeepMotor* motor);
    void SetDeepArm(DeepArm* arm);
    void SetGimbal(Gimbal_t* gimbal);
    void SetLedStrip(CircularStrip* led_strip);
    void SetCamera(Esp32Camera* camera);
    
    // 设置状态回调
    void SetStatusCallback(std::function<void(const std::string&, const std::string&)> callback);
    
    // 处理远程控制命令
    void HandleCommand(const RemoteControlCommand& command);
    
    // 获取支持的命令列表
    std::string GetSupportedCommands() const;
    
private:
    DeepMotor* deep_motor_;
    DeepArm* deep_arm_;
    Gimbal_t* gimbal_;
    CircularStrip* led_strip_;
    Esp32Camera* camera_;
    
    std::function<void(const std::string&, const std::string&)> status_callback_;
    
    // 命令处理函数
    void HandleLedCommand(const RemoteControlCommand& command);
    void HandleMotorCommand(const RemoteControlCommand& command);
    void HandleArmCommand(const RemoteControlCommand& command);
    void HandleGimbalCommand(const RemoteControlCommand& command);
    void HandleCameraCommand(const RemoteControlCommand& command);
    void HandleSystemCommand(const RemoteControlCommand& command);
    
    // 辅助函数
    void SendStatus(const std::string& status, const std::string& message);
    bool ParseIntParameter(const cJSON* params, const std::string& key, int& value);
    bool ParseFloatParameter(const cJSON* params, const std::string& key, float& value);
    bool ParseStringParameter(const cJSON* params, const std::string& key, std::string& value);
    bool ParseBoolParameter(const cJSON* params, const std::string& key, bool& value);
    
    // 常量定义
    static constexpr const char* CMD_LED = "led";
    static constexpr const char* CMD_MOTOR = "motor";
    static constexpr const char* CMD_ARM = "arm";
    static constexpr const char* CMD_GIMBAL = "gimbal";
    static constexpr const char* CMD_CAMERA = "camera";
    static constexpr const char* CMD_SYSTEM = "system";
    
    // LED命令
    static constexpr const char* ACTION_LED_ON = "on";
    static constexpr const char* ACTION_LED_OFF = "off";
    static constexpr const char* ACTION_LED_COLOR = "color";
    static constexpr const char* ACTION_LED_BRIGHTNESS = "brightness";
    static constexpr const char* ACTION_LED_EFFECT = "effect";
    
    // 电机命令
    static constexpr const char* ACTION_MOTOR_START = "start";
    static constexpr const char* ACTION_MOTOR_STOP = "stop";
    static constexpr const char* ACTION_MOTOR_SET_SPEED = "set_speed";
    static constexpr const char* ACTION_MOTOR_SET_POSITION = "set_position";
    
    // 机械臂命令
    static constexpr const char* ACTION_ARM_HOME = "home";
    static constexpr const char* ACTION_ARM_MOVE = "move";
    static constexpr const char* ACTION_ARM_GRIP = "grip";
    static constexpr const char* ACTION_ARM_RELEASE = "release";
    
    // 云台命令
    static constexpr const char* ACTION_GIMBAL_PAN = "pan";
    static constexpr const char* ACTION_GIMBAL_TILT = "tilt";
    static constexpr const char* ACTION_GIMBAL_RESET = "reset";
    
    // 摄像头命令
    static constexpr const char* ACTION_CAMERA_CAPTURE = "capture";
    static constexpr const char* ACTION_CAMERA_START_STREAM = "start_stream";
    static constexpr const char* ACTION_CAMERA_STOP_STREAM = "stop_stream";
    
    // 系统命令
    static constexpr const char* ACTION_SYSTEM_RESTART = "restart";
    static constexpr const char* ACTION_SYSTEM_STATUS = "status";
    static constexpr const char* ACTION_SYSTEM_INFO = "info";
};

#endif // REMOTE_CONTROL_HANDLER_H

