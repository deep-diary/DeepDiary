/**
 * @file board_extensions.cc
 * @brief ATK-DNESP32S3 板级扩展功能实现
 */

#include "board_extensions.h"
#include "config.h"
#include "esp32_camera.h"
#include "display/lcd_display.h"
#include "led/circular_strip.h"
#include "mcp_server.h"

// 模块头文件
#include "can/ESP32-TWAI-CAN.hpp"
#include "motor/protocol_motor.h"
#include "motor/deep_motor.h"
#include "motor/deep_motor_control.h"
#include "led/led_control.h"
#include "arm/deep_arm.h"
#include "arm/deep_arm_control.h"
#include "sensor/QMA6100P/qma6100p.h"
#include "gimbal/gimbal_control.h"

#if ENABLE_MJPEG_FEATURE
#include "streaming/mjpeg_server.h"
#endif

#include <esp_log.h>
#include <esp_camera.h>

#define TAG "board_ext"

// ==================== XL9555 实现 ====================

XL9555::XL9555(i2c_master_bus_handle_t i2c_bus, uint8_t addr) 
    : I2cDevice(i2c_bus, addr) {
    WriteReg(0x06, 0x03);
    WriteReg(0x07, 0xF0);
}

void XL9555::SetOutputState(uint8_t bit, uint8_t level) {
    uint16_t data;
    int index = bit;

    if (bit < 8) {
        data = ReadReg(0x02);
    } else {
        data = ReadReg(0x03);
        index -= 8;
    }

    data = (data & ~(1 << index)) | (level << index);

    if (bit < 8) {
        WriteReg(0x02, data);
    } else {
        WriteReg(0x03, data);
    }
}

// ==================== BoardExtensions 实现 ====================

BoardExtensions::BoardExtensions(i2c_master_bus_handle_t i2c_bus, LcdDisplay* display)
    : i2c_bus_(i2c_bus)
    , display_(display)
    , xl9555_(nullptr)
    , camera_(nullptr)
    , gimbal_(nullptr)
    , led_strip_(nullptr)
    , deep_motor_(nullptr)
    , deep_arm_(nullptr)
    , led_control_(nullptr)
    , deep_motor_control_(nullptr)
    , qma6100p_initialized_(false)
    , can_receive_task_handle_(nullptr)
    , user_main_loop_task_handle_(nullptr)
    , arm_status_update_task_handle_(nullptr) {
    
    ESP_LOGI(TAG, "板级扩展功能初始化开始...");
    
    // 初始化XL9555
    InitializeXL9555();
    
    // 初始化摄像头
    camera_ = InitializeCamera();
    
    // 初始化云台
    InitializeGimbal();
    
    // 初始化LED灯带和CAN
#if ENABLE_CAN_FEATURE || ENABLE_LED_STRIP_FEATURE
    InitializeWs2812();
    InitializeCan();
#endif
    
    // 初始化传感器
    InitializeQMA6100P();
    
    // 初始化控制接口
    InitializeControls();
    
    // 启动用户主循环
    StartUserMainLoop();
    
    ESP_LOGI(TAG, "板级扩展功能初始化完成");
}

BoardExtensions::~BoardExtensions() {
    ESP_LOGI(TAG, "清理板级扩展资源...");
    
    // 删除任务
    if (user_main_loop_task_handle_) {
        vTaskDelete(user_main_loop_task_handle_);
    }
    if (can_receive_task_handle_) {
        vTaskDelete(can_receive_task_handle_);
    }
    if (arm_status_update_task_handle_) {
        vTaskDelete(arm_status_update_task_handle_);
    }
    
    // 删除控制类
    delete led_control_;
    delete deep_motor_control_;
    
    // 删除硬件对象
    delete deep_arm_;
    delete deep_motor_;
    delete led_strip_;
    
    // 清理云台
    if (gimbal_) {
        Gimbal_deinit(gimbal_);
        free(gimbal_);
    }
    
    delete camera_;
    delete xl9555_;
}

void BoardExtensions::InitializeXL9555() {
    ESP_LOGI(TAG, "初始化XL9555 I/O扩展...");
    xl9555_ = new XL9555(i2c_bus_, 0x20);
    ESP_LOGI(TAG, "XL9555初始化完成");
}

Camera* BoardExtensions::InitializeCamera() {
#if ENABLE_CAMERA_FEATURE
    ESP_LOGI(TAG, "初始化相机功能...");
    
    if (!xl9555_) {
        ESP_LOGE(TAG, "XL9555未初始化，无法控制摄像头");
        return nullptr;
    }
    
    xl9555_->SetOutputState(OV_PWDN_IO, 0);   // PWDN=低 (上电)
    vTaskDelay(pdMS_TO_TICKS(100));
    xl9555_->SetOutputState(OV_RESET_IO, 0);  // 确保复位
    vTaskDelay(pdMS_TO_TICKS(100));
    xl9555_->SetOutputState(OV_RESET_IO, 1);  // 释放复位
    vTaskDelay(pdMS_TO_TICKS(200));

    camera_config_t config = {};
    config.pin_pwdn = CAM_PIN_PWDN;
    config.pin_reset = CAM_PIN_RESET;
    config.pin_xclk = CAM_PIN_XCLK;
    config.pin_sccb_sda = CAM_PIN_SIOD;
    config.pin_sccb_scl = CAM_PIN_SIOC;
    config.pin_d7 = CAM_PIN_D7;
    config.pin_d6 = CAM_PIN_D6;
    config.pin_d5 = CAM_PIN_D5;
    config.pin_d4 = CAM_PIN_D4;
    config.pin_d3 = CAM_PIN_D3;
    config.pin_d2 = CAM_PIN_D2;
    config.pin_d1 = CAM_PIN_D1;
    config.pin_d0 = CAM_PIN_D0;
    config.pin_vsync = CAM_PIN_VSYNC;
    config.pin_href = CAM_PIN_HREF;
    config.pin_pclk = CAM_PIN_PCLK;
    config.xclk_freq_hz = 10000000;
    config.ledc_timer = LEDC_TIMER_0;
    config.ledc_channel = LEDC_CHANNEL_0;
    config.pixel_format = PIXFORMAT_RGB565;
    config.frame_size = FRAMESIZE_QVGA;
    config.jpeg_quality = 12;
    config.fb_count = 1;
    config.fb_location = CAMERA_FB_IN_PSRAM;
    config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;

    esp_err_t err = esp_camera_init(&config);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Camera init failed: %s", esp_err_to_name(err));
        return nullptr;
    }
    
    esp_camera_deinit();
    Camera* cam = new Esp32Camera(config);
    
    // 修复图像倒置问题
    cam->SetVFlip(true);
    ESP_LOGI(TAG, "相机垂直翻转已启用");
    
    ESP_LOGI(TAG, "相机功能初始化完成");
    return cam;
#else
    ESP_LOGI(TAG, "相机功能已禁用");
    return nullptr;
#endif
}

void BoardExtensions::InitializeGimbal() {
    ESP_LOGI(TAG, "初始化云台...");
    
    gimbal_ = (Gimbal_t*)malloc(sizeof(Gimbal_t));
    if (Gimbal_init(gimbal_, SERVO_PAN_GPIO, SERVO_TILT_GPIO) != ESP_OK) {
        ESP_LOGE(TAG, "云台初始化失败!");
        free(gimbal_);
        gimbal_ = nullptr;
        return;
    }
    
    Gimbal_setAngles(gimbal_, 135, 90);
    ESP_LOGI(TAG, "云台初始化完成 - PAN: GPIO%d, TILT: GPIO%d", 
             SERVO_PAN_GPIO, SERVO_TILT_GPIO);
}

void BoardExtensions::InitializeWs2812() {
#if ENABLE_LED_STRIP_FEATURE
    ESP_LOGI(TAG, "初始化WS2812灯带...GPIO=%d, LED数量=%d", 
             WS2812_STRIP_GPIO, WS2812_LED_COUNT);
    led_strip_ = new CircularStrip(WS2812_STRIP_GPIO, WS2812_LED_COUNT);
#else
    ESP_LOGI(TAG, "WS2812灯带功能已禁用");
#endif
}

void BoardExtensions::InitializeCan() {
#if ENABLE_CAN_FEATURE
    ESP_LOGI(TAG, "初始化CAN总线...TX=%d, RX=%d", CAN_TX_GPIO, CAN_RX_GPIO);
    
    deep_motor_ = new DeepMotor(led_strip_);
    
    uint8_t motor_ids[6] = {1, 2, 3, 4, 5, 6};
    deep_arm_ = new DeepArm(deep_motor_, motor_ids);
    
    if (ESP32Can.begin(ESP32Can.convertSpeed(1000), CAN_TX_GPIO, CAN_RX_GPIO, 10, 10)) {
        ESP_LOGI(TAG, "CAN总线启动成功!");
        
        BaseType_t ret = xTaskCreate(can_receive_task, "can_receive", 
                                     4096, this, 5, &can_receive_task_handle_);
        if (ret != pdPASS) {
            ESP_LOGE(TAG, "创建CAN接收任务失败!");
        } else {
            ESP_LOGI(TAG, "CAN接收任务创建成功!");
        }
    } else {
        ESP_LOGE(TAG, "CAN总线启动失败!");
    }
#else
    ESP_LOGI(TAG, "CAN总线功能已禁用");
#endif
}

void BoardExtensions::InitializeQMA6100P() {
#if ENABLE_QMA6100P_FEATURE
    ESP_LOGI(TAG, "初始化QMA6100P加速度计...");
    
    esp_err_t ret = qma6100p_init(i2c_bus_);
    if (ret == ESP_OK) {
        qma6100p_initialized_ = true;
        ESP_LOGI(TAG, "QMA6100P加速度计初始化成功!");
    } else {
        qma6100p_initialized_ = false;
        ESP_LOGW(TAG, "QMA6100P加速度计初始化失败");
    }
#else
    ESP_LOGI(TAG, "QMA6100P加速度计功能已禁用");
#endif
}

void BoardExtensions::InitializeControls() {
#if ENABLE_LED_STRIP_FEATURE || ENABLE_CAN_FEATURE
    auto& mcp_server = McpServer::GetInstance();
#endif
    
#if ENABLE_LED_STRIP_FEATURE
    led_control_ = new LedStripControl(led_strip_, mcp_server);
    ESP_LOGI(TAG, "LED灯带控制类初始化完成");
#endif

#if ENABLE_CAN_FEATURE
    deep_motor_control_ = new DeepMotorControl(deep_motor_, mcp_server);
    ESP_LOGI(TAG, "电机控制类初始化完成");
#endif

#if ENABLE_MJPEG_FEATURE && ENABLE_CAMERA_FEATURE
    InitializeMjpegServer();
#endif
    
    ESP_LOGI(TAG, "控制类初始化完成");
}

#if ENABLE_MJPEG_FEATURE
void BoardExtensions::InitializeMjpegServer() {
    if (!camera_) {
        ESP_LOGI(TAG, "相机未初始化，跳过MJPEG服务器");
        return;
    }
    
    mjpeg_server_ = std::make_unique<MjpegServer>(8080);
    mjpeg_server_->SetFrameRate(10);
    mjpeg_server_->SetJpegQuality(80);
    
    ESP_LOGI(TAG, "MJPEG服务器对象创建完成");
}
#endif

void BoardExtensions::StartUserMainLoop() {
    BaseType_t ret = xTaskCreate(
        user_main_loop_task,
        "user_main_loop",
        8192,
        this,
        4,
        &user_main_loop_task_handle_
    );
    
    if (ret != pdPASS) {
        ESP_LOGE(TAG, "创建用户主循环任务失败!");
    } else {
        ESP_LOGI(TAG, "用户主循环任务创建成功!");
    }
}

#if ENABLE_MJPEG_FEATURE
void BoardExtensions::StartMjpegServerWhenReady() {
    if (!mjpeg_server_) {
        ESP_LOGW(TAG, "MJPEG服务器对象未创建");
        return;
    }
    
    if (mjpeg_server_->IsRunning()) {
        ESP_LOGI(TAG, "MJPEG服务器已在运行");
        return;
    }
    
    ESP_LOGI(TAG, "WiFi已连接，启动MJPEG服务器...");
    vTaskDelay(pdMS_TO_TICKS(2000));
    
    if (mjpeg_server_->Start()) {
        ESP_LOGI(TAG, "MJPEG服务器启动成功");
        ESP_LOGI(TAG, "访问地址: %s", mjpeg_server_->GetUrl().c_str());
    } else {
        ESP_LOGE(TAG, "MJPEG服务器启动失败");
    }
}
#endif

// ==================== 任务函数 ====================

void BoardExtensions::can_receive_task(void* pvParameters) {
    BoardExtensions* ext = static_cast<BoardExtensions*>(pvParameters);
    CanFrame rxFrame;
    
    ESP_LOGI(TAG, "CAN接收任务启动");
    
    while (1) {
        if (ESP32Can.readFrame(rxFrame, 1000)) {
            if (ext->deep_motor_ && ext->deep_motor_->processCanFrame(rxFrame)) {
                // 电机反馈帧已处理
            } else if (rxFrame.identifier == CAN_CMD_SERVO_CONTROL) {
                if (ext->gimbal_) {
                    Gimbal_handleCanCommand(ext->gimbal_, &rxFrame);
                }
            }
        }
        vTaskDelay(pdMS_TO_TICKS(10));
    }
}

void BoardExtensions::user_main_loop_task(void* pvParameters) {
    BoardExtensions* ext = static_cast<BoardExtensions*>(pvParameters);
    
    ESP_LOGI(TAG, "用户主循环任务启动");
    
    qma6100p_rawdata_t accel_data;
    uint8_t update_counter = 0;
    char msg_buffer[256];
    
    while (1) {
        vTaskDelay(pdMS_TO_TICKS(10));
        update_counter++;
        
        // 每 500ms 更新一次加速度计数据（降低更新频率以减少内存压力）
        if (update_counter >= 50 && ext->qma6100p_initialized_) {
            update_counter = 0;
            
            qma6100p_read_rawdata(&accel_data);
            
            // 格式化加速度计数据（两行显示）
            snprintf(msg_buffer, sizeof(msg_buffer),
                     "X:%.1f Y:%.1f Z:%.1f\n俯仰:%.0f° 翻滚:%.0f°",
                     accel_data.acc_x, accel_data.acc_y, accel_data.acc_z,
                     accel_data.pitch, accel_data.roll);
            
            // 使用 SetChatMessage 显示在对话区域
            if (ext->display_ != nullptr) {
                ext->display_->SetChatMessage("system", msg_buffer);
            }
            
            ESP_LOGI(TAG, "ACC[%.2f, %.2f, %.2f] Pitch:%.1f° Roll:%.1f°", 
                     accel_data.acc_x, accel_data.acc_y, accel_data.acc_z,
                     accel_data.pitch, accel_data.roll);
        }
    }
}

void BoardExtensions::arm_status_update_task(void* pvParameters) {
    BoardExtensions* ext = static_cast<BoardExtensions*>(pvParameters);
    (void)ext;
    
    while (1) {
        // 机械臂状态更新逻辑（预留）
        vTaskDelay(pdMS_TO_TICKS(500));
    }
}

