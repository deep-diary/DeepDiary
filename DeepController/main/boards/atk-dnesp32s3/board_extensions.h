/**
 * @file board_extensions.h
 * @brief ATK-DNESP32S3 板级扩展功能
 * 
 * 本文件包含所有自定义的新增功能，与开源项目的主板级文件分离，
 * 便于维护和升级开源项目代码。
 */

#ifndef BOARD_EXTENSIONS_H
#define BOARD_EXTENSIONS_H

#include <esp_err.h>
#include <driver/i2c_master.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <memory>
#include "i2c_device.h"
#include "config.h"  // 必须在前面包含，以便使用功能开关宏
#include "gimbal/Gimbal.h"  // Gimbal_t 是 C 结构体，需要完整定义

// 前向声明
class CircularStrip;
class DeepMotor;
class DeepArm;
class LedStripControl;
class DeepMotorControl;
class Esp32Camera;
class Camera;
class LcdDisplay;

#if ENABLE_MJPEG_FEATURE
class MjpegServer;
#endif

/**
 * @brief XL9555 I/O扩展芯片驱动类
 */
class XL9555 : public I2cDevice {
public:
    XL9555(i2c_master_bus_handle_t i2c_bus, uint8_t addr);
    void SetOutputState(uint8_t bit, uint8_t level);
};

/**
 * @brief 板级扩展功能管理类
 * 
 * 将所有自定义的新增功能集中在这个类中管理，包括：
 * - XL9555 I/O扩展
 * - 摄像头控制
 * - 云台控制
 * - CAN总线和电机
 * - LED灯带
 * - 传感器
 * - 流媒体服务
 */
class BoardExtensions {
public:
    /**
     * @brief 构造函数
     * @param i2c_bus I2C总线句柄
     * @param display 显示屏对象指针（可选）
     */
    BoardExtensions(i2c_master_bus_handle_t i2c_bus, LcdDisplay* display = nullptr);
    
    /**
     * @brief 析构函数 - 清理所有资源
     */
    ~BoardExtensions();
    
    // ========== 初始化方法 ==========
    
    /**
     * @brief 初始化XL9555 I/O扩展芯片
     */
    void InitializeXL9555();
    
    /**
     * @brief 初始化摄像头（需要XL9555控制电源和复位）
     * @return 摄像头对象指针，失败返回nullptr
     */
    Camera* InitializeCamera();
    
    /**
     * @brief 初始化云台舵机
     */
    void InitializeGimbal();
    
    /**
     * @brief 初始化WS2812 LED灯带
     */
    void InitializeWs2812();
    
    /**
     * @brief 初始化CAN总线和电机系统
     */
    void InitializeCan();
    
    /**
     * @brief 初始化QMA6100P加速度计
     */
    void InitializeQMA6100P();
    
    /**
     * @brief 初始化所有MCP控制接口
     */
    void InitializeControls();
    
    /**
     * @brief 启动用户主循环任务（传感器数据采集等）
     */
    void StartUserMainLoop();
    
#if ENABLE_MJPEG_FEATURE
    /**
     * @brief 初始化MJPEG视频流服务器（可通过ENABLE_MJPEG_FEATURE宏启用）
     */
    void InitializeMjpegServer();
    
    /**
     * @brief WiFi连接后启动MJPEG服务器
     */
    void StartMjpegServerWhenReady();
#endif
    
    /**
     * @brief 设置显示屏指针（用于后期绑定）
     * @param display 显示屏对象指针
     */
    void SetDisplay(LcdDisplay* display) { display_ = display; }
    
    // ========== 访问器方法 ==========
    
    /**
     * @brief 获取XL9555对象
     */
    XL9555* GetXL9555() { return xl9555_; }
    
    /**
     * @brief 获取摄像头对象
     */
    Camera* GetCamera() { return camera_; }
    
    /**
     * @brief 获取云台对象
     */
    Gimbal_t* GetGimbal() { return gimbal_; }
    
    /**
     * @brief 获取电机管理器
     */
    DeepMotor* GetDeepMotor() { return deep_motor_; }
    
    /**
     * @brief 获取机械臂控制器
     */
    DeepArm* GetDeepArm() { return deep_arm_; }
    
    /**
     * @brief 获取LED灯带
     */
    CircularStrip* GetLedStrip() { return led_strip_; }
    
#if ENABLE_MJPEG_FEATURE
    /**
     * @brief 获取MJPEG服务器
     */
    MjpegServer* GetMjpegServer() { return mjpeg_server_.get(); }
#endif
    
    /**
     * @brief 检查QMA6100P是否初始化成功
     */
    bool IsQMA6100PInitialized() const { return qma6100p_initialized_; }

private:
    // ========== 硬件资源 ==========
    i2c_master_bus_handle_t i2c_bus_;      // I2C总线句柄
    LcdDisplay* display_;                   // 显示屏对象（外部管理）
    
    // ========== I/O扩展 ==========
    XL9555* xl9555_;                        // XL9555 I/O扩展芯片
    
    // ========== 外设对象 ==========
    Camera* camera_;                        // 摄像头（实际类型：Esp32Camera*，通过基类指针管理）
    Gimbal_t* gimbal_;                      // 云台
    CircularStrip* led_strip_;              // WS2812灯带
    
    // ========== 电机系统 ==========
    DeepMotor* deep_motor_;                 // 电机管理器
    DeepArm* deep_arm_;                     // 机械臂控制器
    
    // ========== 控制接口 ==========
    LedStripControl* led_control_;          // LED控制
    DeepMotorControl* deep_motor_control_;  // 电机控制
    // GimbalControl* gimbal_control_;      // 云台控制（预留）
    // DeepArmControl* deep_arm_control_;   // 机械臂控制（预留）
    
    // ========== 流媒体服务 ==========
#if ENABLE_MJPEG_FEATURE
    std::unique_ptr<MjpegServer> mjpeg_server_;  // MJPEG视频流服务器
#endif
    
    // ========== 传感器 ==========
    bool qma6100p_initialized_;             // QMA6100P初始化状态
    
    // ========== 任务句柄 ==========
    TaskHandle_t can_receive_task_handle_;        // CAN接收任务
    TaskHandle_t user_main_loop_task_handle_;     // 用户主循环任务
    TaskHandle_t arm_status_update_task_handle_;  // 机械臂状态更新任务
    
    // ========== 静态任务函数 ==========
    
    /**
     * @brief CAN接收任务
     */
    static void can_receive_task(void* pvParameters);
    
    /**
     * @brief 用户主循环任务
     */
    static void user_main_loop_task(void* pvParameters);
    
    /**
     * @brief 机械臂状态更新任务
     */
    static void arm_status_update_task(void* pvParameters);
};

#endif // BOARD_EXTENSIONS_H

