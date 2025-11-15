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
#if ENABLE_SERVO_FEATURE
#include "gimbal/gimbal_control.h"
#endif

// MQTT相关头文件
#include "mqtt/user_mqtt_config.h"
#include "mqtt/user_mqtt_client.h"
#include "mqtt/remote_control_handler.h"
#include "mqtt/device_info_collector.h"

#if ENABLE_MJPEG_FEATURE
#include "streaming/mjpeg_server.h"
#endif

#if ENABLE_TCP_CLIENT_MODE
extern "C" {
#include "streaming/tcp_client.h"
}
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
#if ENABLE_SERVO_FEATURE
    , gimbal_(nullptr)
#endif
    , led_strip_(nullptr)
    , deep_motor_(nullptr)
    , deep_arm_(nullptr)
    , led_control_(nullptr)
    , deep_motor_control_(nullptr)
#if ENABLE_SERVO_FEATURE
    , gimbal_control_(nullptr)
#endif
    , qma6100p_initialized_(false)
    , user_mqtt_initialized_(false)
    , can_receive_task_handle_(nullptr)
    , user_main_loop_task_handle_(nullptr)
    , arm_status_update_task_handle_(nullptr) {
    
    ESP_LOGI(TAG, "板级扩展功能初始化开始...");
    
    // 初始化XL9555
    InitializeXL9555();
    
    // 初始化摄像头
    camera_ = InitializeCamera();
    
    // 初始化云台
#if ENABLE_SERVO_FEATURE
    InitializeGimbal();
#endif
    
    // 初始化CAN总线
#if ENABLE_CAN_FEATURE
    InitializeCan();
#endif
    
    InitializeWs2812();

    // 初始化传感器
    InitializeQMA6100P();
    
    // 初始化控制接口
    InitializeControls();
    
    // 初始化用户MQTT客户端
    InitializeUserMqtt();
    
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
#if ENABLE_SERVO_FEATURE
    delete gimbal_control_;
#endif
    
    // 删除硬件对象
    delete deep_arm_;
    delete deep_motor_;
    delete led_strip_;
    
    // 清理云台
#if ENABLE_SERVO_FEATURE
    if (gimbal_) {
        Gimbal_deinit(gimbal_);
        free(gimbal_);
    }
#endif
    
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
    
#if ENABLE_TCP_CLIENT_MODE
    // TCP 客户端模式需要 JPEG 格式
    config.pixel_format = PIXFORMAT_JPEG;
    config.frame_size = FRAMESIZE_QVGA;
    config.jpeg_quality = 12;  // 0-63，数值越小质量越高
    config.fb_count = 2;       // 使用双缓冲提高性能
#else
    // MJPEG 服务器或显示模式使用 RGB565
    config.pixel_format = PIXFORMAT_RGB565;
    config.frame_size = FRAMESIZE_QVGA;
    config.jpeg_quality = 12;
    config.fb_count = 1;
#endif
    
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

#if ENABLE_SERVO_FEATURE
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
#endif

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
#if ENABLE_LED_STRIP_FEATURE || ENABLE_CAN_FEATURE || ENABLE_SERVO_FEATURE
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

#if ENABLE_SERVO_FEATURE
    if (gimbal_) {
        gimbal_control_ = new GimbalControl(gimbal_, mcp_server);
        ESP_LOGI(TAG, "云台控制类初始化完成");
    } else {
        ESP_LOGW(TAG, "云台未初始化，跳过云台控制类初始化");
    }
#endif

#if ENABLE_MJPEG_FEATURE && ENABLE_CAMERA_FEATURE
    InitializeMjpegServer();
#endif

#if ENABLE_TCP_CLIENT_MODE && ENABLE_CAMERA_FEATURE
    InitializeTcpClient();
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

#if ENABLE_TCP_CLIENT_MODE
void BoardExtensions::InitializeTcpClient() {
    if (!camera_) {
        ESP_LOGI(TAG, "相机未初始化，跳过TCP客户端");
        return;
    }
    
    // 配置TCP客户端
    tcp_client_config_t config = {
        .server_ip = TCP_SERVER_IP,
        .server_port = TCP_SERVER_PORT,
        .auto_reconnect = true,
        .reconnect_interval = 3000
    };
    
    strncpy(config.server_ip, TCP_SERVER_IP, sizeof(config.server_ip) - 1);
    config.server_port = TCP_SERVER_PORT;
    
    esp_err_t ret = tcp_client_init(&config);
    if (ret == ESP_OK) {
        ESP_LOGI(TAG, "TCP客户端初始化完成");
    } else {
        ESP_LOGE(TAG, "TCP客户端初始化失败");
    }
}

void BoardExtensions::StartTcpClientWhenReady() {
    // TCP客户端不再自动启动，改为按需启动（通过tar_cam_switch控制）
    // 这样可以节省流量，只在需要推流时才连接
    ESP_LOGI(TAG, "TCP客户端已初始化，等待控制指令启动推流");
    ESP_LOGI(TAG, "连接目标: %s:%d", TCP_SERVER_IP, TCP_SERVER_PORT);
    ESP_LOGI(TAG, "提示: 通过MQTT发送tar_cam_switch=true来启动推流");
}
#endif

// ==================== 任务函数 ====================

void BoardExtensions::can_receive_task(void* pvParameters) {
    BoardExtensions* ext = static_cast<BoardExtensions*>(pvParameters);
    CanFrame rxFrame;
    
    ESP_LOGI(TAG, "CAN接收任务启动");
    
    while (1) {
        if (ESP32Can.readFrame(rxFrame, 1000)) {
            ESP_LOGI(TAG, "收到CAN帧: ID=0x%08lX, 长度=%d", rxFrame.identifier, rxFrame.data_length_code);
            if (ext->deep_motor_ && ext->deep_motor_->processCanFrame(rxFrame)) {
                // 电机反馈帧已处理
            }
#if ENABLE_SERVO_FEATURE
            else if (rxFrame.identifier == CAN_CMD_SERVO_CONTROL) {
                if (ext->gimbal_) {
                    Gimbal_handleCanCommand(ext->gimbal_, &rxFrame);
                }
            }
#endif
        }
        vTaskDelay(pdMS_TO_TICKS(10));
    }
}

void BoardExtensions::user_main_loop_task(void* pvParameters) {
    BoardExtensions* ext = static_cast<BoardExtensions*>(pvParameters);
    
    ESP_LOGI(TAG, "用户主循环任务启动");
    
    qma6100p_rawdata_t accel_data;
    char msg_buffer[256];
    
    // ==================== 计数器初始化 ====================
    static uint32_t cycle_counter = 0;
    static bool first_run = true;
    
    // ==================== 时间标志位 ====================
    struct TimeFlags {
        bool display_update;
        bool thumbler_status;
        
        void clear() {
            display_update = false;
            thumbler_status = false;
        }
    } time_flags;
    
    time_flags.clear();
    
    while (1) {
        vTaskDelay(pdMS_TO_TICKS(MAIN_LOOP_BASE_DELAY_MS));
        
        // 首次运行后增加计数器，避免cycle_counter=0时立即触发所有任务
        if (!first_run) {
            cycle_counter++;
        } else {
            first_run = false;
        }
        
        // 防止计数器溢出（重新开始计数不影响周期性任务）
        // 使用所有任务周期中的最大值，确保所有周期性任务都能正确触发
        if (cycle_counter > MAX_TASK_CYCLE) { 
            cycle_counter = 1; // 重置为1而不是0，避免立即触发
        }
        
        // ==================== 时间标志位判断 ====================
        // 由于主循环基础延时是100ms，所以使用倍数即可
        time_flags.clear();
        
        // 设置各个标志位（使用取模运算判断是否到达指定周期）
        if ((cycle_counter % DISPLAY_UPDATE_CYCLE) == 0) {
            time_flags.display_update = true;
        }
        
        if ((cycle_counter % THUMBLER_STATUS_CYCLE) == 0) {
            time_flags.thumbler_status = true;
        }
        
        // ==================== 执行任务（根据标志位）====================
        
        // 显示更新任务
        if (time_flags.display_update && ext->qma6100p_initialized_) {
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
        }
        
        // MQTT任务（仅在连接时执行）- 只发送不倒翁状态
        if (ext->user_mqtt_client_ && ext->user_mqtt_client_->IsConnected() && ext->device_info_collector_) {
            // 不倒翁状态发送任务（使用 Thumbler 协议）
            if (time_flags.thumbler_status) {
                ESP_LOGI(TAG, "📡 SENDING Thumbler Status");
                DeviceStatus::ThumblerStatus thumbler_status = ext->device_info_collector_->CollectThumblerStatus();
                if (ext->user_mqtt_client_->SendThumblerStatus(thumbler_status)) {
                    // ESP_LOGI(TAG, "✅ Thumbler status sent successfully");
                }
            }
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

// ==================== 用户MQTT功能实现 ====================

void BoardExtensions::InitializeUserMqtt() {
    ESP_LOGI(TAG, "初始化用户MQTT客户端...");
    
    try {
        // 创建MQTT客户端
        user_mqtt_client_ = std::make_unique<UserMqttClient>();
        
        // 创建远程控制处理器
        remote_control_handler_ = std::make_unique<RemoteControlHandler>();
        
        // 创建设备信息收集器
        device_info_collector_ = std::make_unique<DeviceInfoCollector>();
        
        // 设置设备组件引用
        if (remote_control_handler_) {
            remote_control_handler_->SetDeepMotor(deep_motor_);
            remote_control_handler_->SetDeepArm(deep_arm_);
#if ENABLE_SERVO_FEATURE
            remote_control_handler_->SetGimbal(gimbal_);
#endif
            remote_control_handler_->SetLedStrip(led_strip_);
#if ENABLE_LED_STRIP_FEATURE
            remote_control_handler_->SetLedControl(led_control_);
#endif
            remote_control_handler_->SetCamera(static_cast<Esp32Camera*>(camera_));
        }
        
        if (device_info_collector_) {
            device_info_collector_->SetDeepMotor(deep_motor_);
            device_info_collector_->SetDeepArm(deep_arm_);
#if ENABLE_SERVO_FEATURE
            device_info_collector_->SetGimbal(gimbal_);
#endif
            device_info_collector_->SetLedStrip(led_strip_);
#if ENABLE_LED_STRIP_FEATURE
            device_info_collector_->SetLedControl(led_control_);
#endif
            device_info_collector_->SetCamera(static_cast<Esp32Camera*>(camera_));
        }
        
        // 设置MQTT客户端引用到远程控制处理器（用于发送事件反馈）
        if (remote_control_handler_ && user_mqtt_client_) {
            remote_control_handler_->SetMqttClient(user_mqtt_client_.get());
        }
        
        user_mqtt_initialized_ = true;
        ESP_LOGI(TAG, "用户MQTT客户端初始化完成");
        
    } catch (const std::exception& e) {
        ESP_LOGE(TAG, "用户MQTT客户端初始化失败: %s", e.what());
        user_mqtt_initialized_ = false;
    }
}

void BoardExtensions::StartUserMqtt() {
    if (!user_mqtt_initialized_ || !user_mqtt_client_) {
        ESP_LOGW(TAG, "用户MQTT客户端未初始化，跳过启动");
        return;
    }
    
    ESP_LOGI(TAG, "启动用户MQTT客户端...");
    
    // 等待网络稳定
    ESP_LOGI(TAG, "等待网络稳定...");
    vTaskDelay(pdMS_TO_TICKS(2000)); // 等待2秒
    
    // 从NVS加载配置
    UserMqttConfig::LoadFromNvs();
    
    // 创建配置对象
    UserMqttClientConfig config;
    config.broker_host = UserMqttConfig::GetBrokerHost();
    config.broker_port = UserMqttConfig::GetBrokerPort();
    config.client_id = UserMqttConfig::GetClientId();
    config.username = UserMqttConfig::GetUsername();
    config.password = UserMqttConfig::GetPassword();
    config.keepalive_interval = UserMqttConfig::GetKeepaliveInterval();
    config.use_ssl = UserMqttConfig::GetUseSsl();
    
    // 设置MQTT主题（使用 Thumbler 协议格式）
    std::string device_id = config.client_id; // 设备ID格式：ATK-DNESP32S3-{MAC地址}
    config.status_topic = "Thumbler/" + device_id + "/status";
    config.control_topic = "Thumbler/" + device_id + "/cmd";
    config.event_topic = "Thumbler/" + device_id + "/event";
    
    ESP_LOGI(TAG, "🔧 MQTT Configuration (Thumbler Protocol):");
    ESP_LOGI(TAG, "  Broker: %s:%d", config.broker_host.c_str(), config.broker_port);
    ESP_LOGI(TAG, "  Client ID: %s", config.client_id.c_str());
    ESP_LOGI(TAG, "  Device ID: %s", device_id.c_str());
    ESP_LOGI(TAG, "  Status Topic: %s", config.status_topic.c_str());
    ESP_LOGI(TAG, "  Control Topic: %s", config.control_topic.c_str());
    ESP_LOGI(TAG, "  Event Topic: %s", config.event_topic.c_str());
    
    // 初始化客户端
    if (user_mqtt_client_->Initialize(config)) {
        // 设置 Thumbler 控制回调
        user_mqtt_client_->SetThumblerControlCallback([this](const ThumblerControlCommand& cmd) {
            if (remote_control_handler_) {
                remote_control_handler_->HandleThumblerCommand(cmd);
            }
        });
        
        user_mqtt_client_->SetConnectionCallback([](bool connected) {
            if (connected) {
                ESP_LOGI(TAG, "已连接到用户MQTT服务器");
            } else {
                ESP_LOGW(TAG, "与用户MQTT服务器断开连接");
            }
        });
        
        // 连接MQTT服务器
        if (user_mqtt_client_->Connect()) {
            ESP_LOGI(TAG, "✅ 成功连接到用户MQTT服务器");
        } else {
            ESP_LOGE(TAG, "❌ 连接用户MQTT服务器失败");
        }
    } else {
        ESP_LOGE(TAG, "用户MQTT客户端初始化失败");
    }
}

