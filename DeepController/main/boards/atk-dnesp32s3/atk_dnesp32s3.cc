#include "wifi_board.h"
#include "codecs/es8388_audio_codec.h"
#include "display/lcd_display.h"
#include "application.h"
#include "button.h"
#include "config.h"
#include "i2c_device.h"
#include "led/single_led.h"
#include "led/circular_strip.h"
#include "esp32_camera.h"
#include "mcp_server.h"
#include "Gimbal.h"
#include "ESP32-TWAI-CAN.hpp"
#include "protocol_motor.h"
#include "deep_motor.h"
#include "led_control.h"
#include "deep_motor_control.h"
#include "gimbal_control.h"
#include "deep_arm.h"
#include "deep_arm_control.h"
#include "mjpeg_server.h"

#include <esp_log.h>
#include <esp_lcd_panel_vendor.h>
#include <esp_event.h>
#include <esp_wifi.h>
#include <driver/i2c_master.h>
#include <driver/spi_common.h>
#include <wifi_station.h>
#include <cJSON.h>

#define TAG "atk_dnesp32s3"

class XL9555 : public I2cDevice {
public:
    XL9555(i2c_master_bus_handle_t i2c_bus, uint8_t addr) : I2cDevice(i2c_bus, addr) {
        WriteReg(0x06, 0x03);
        WriteReg(0x07, 0xF0);
    }

    void SetOutputState(uint8_t bit, uint8_t level) {
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
};

class atk_dnesp32s3 : public WifiBoard {
private:
    i2c_master_bus_handle_t i2c_bus_;
    Button boot_button_;
    LcdDisplay* display_;
    XL9555* xl9555_;
    Esp32Camera* camera_;
    Gimbal_t gimbal_;
    
    // CAN相关成员
    TaskHandle_t can_receive_task_handle_;
    TaskHandle_t arm_status_update_task_handle_;  // 机械臂状态更新任务
    DeepMotor* deep_motor_; // 深度电机管理器
    DeepArm* deep_arm_;     // 机械臂控制器
    
    // 2812灯带相关成员
    CircularStrip* led_strip_;
    
    // 控制类成员
    LedStripControl* led_control_;        // LED控制
    DeepMotorControl* deep_motor_control_; // 电机控制
    // GimbalControl* gimbal_control_;       // 临时屏蔽舵机控制
    // DeepArmControl* deep_arm_control_;      // 机械臂MCP控制
    
    // MJPEG服务器成员
    std::unique_ptr<MjpegServer> mjpeg_server_;

    void InitializeI2c() {
        // Initialize I2C peripheral
        i2c_master_bus_config_t i2c_bus_cfg = {
            .i2c_port = (i2c_port_t)I2C_NUM_0,
            .sda_io_num = AUDIO_CODEC_I2C_SDA_PIN,
            .scl_io_num = AUDIO_CODEC_I2C_SCL_PIN,
            .clk_source = I2C_CLK_SRC_DEFAULT,
            .glitch_ignore_cnt = 7,
            .intr_priority = 0,
            .trans_queue_depth = 0,
            .flags = {
                .enable_internal_pullup = 1,
            },
        };
        ESP_ERROR_CHECK(i2c_new_master_bus(&i2c_bus_cfg, &i2c_bus_));

        // Initialize XL9555
        xl9555_ = new XL9555(i2c_bus_, 0x20);
    }

    // Initialize spi peripheral
    void InitializeSpi() {
        spi_bus_config_t buscfg = {};
        buscfg.mosi_io_num = LCD_MOSI_PIN;
        buscfg.miso_io_num = GPIO_NUM_NC;
        buscfg.sclk_io_num = LCD_SCLK_PIN;
        buscfg.quadwp_io_num = GPIO_NUM_NC;
        buscfg.quadhd_io_num = GPIO_NUM_NC;
        buscfg.max_transfer_sz = DISPLAY_WIDTH * DISPLAY_HEIGHT * sizeof(uint16_t);
        ESP_ERROR_CHECK(spi_bus_initialize(SPI2_HOST, &buscfg, SPI_DMA_CH_AUTO));
    }

    void InitializeButtons() {
        boot_button_.OnClick([this]() {
            auto& app = Application::GetInstance();
            if (app.GetDeviceState() == kDeviceStateStarting && !WifiStation::GetInstance().IsConnected()) {
                ResetWifiConfiguration();
            }
            app.ToggleChatState();
        });
    }

    void InitializeSt7789Display() {
        esp_lcd_panel_io_handle_t panel_io = nullptr;
        esp_lcd_panel_handle_t panel = nullptr;
        ESP_LOGD(TAG, "Install panel IO");
        // 液晶屏控制IO初始化
        esp_lcd_panel_io_spi_config_t io_config = {};
        io_config.cs_gpio_num = LCD_CS_PIN;
        io_config.dc_gpio_num = LCD_DC_PIN;
        io_config.spi_mode = 0;
        io_config.pclk_hz = 20 * 1000 * 1000;
        io_config.trans_queue_depth = 7;
        io_config.lcd_cmd_bits = 8;
        io_config.lcd_param_bits = 8;
        esp_lcd_new_panel_io_spi(SPI2_HOST, &io_config, &panel_io);

        // 初始化液晶屏驱动芯片ST7789
        ESP_LOGD(TAG, "Install LCD driver");
        esp_lcd_panel_dev_config_t panel_config = {};
        panel_config.reset_gpio_num = GPIO_NUM_NC;
        panel_config.rgb_ele_order = LCD_RGB_ELEMENT_ORDER_RGB;
        panel_config.bits_per_pixel = 16;
        panel_config.data_endian = LCD_RGB_DATA_ENDIAN_BIG,
        esp_lcd_new_panel_st7789(panel_io, &panel_config, &panel);
        
        esp_lcd_panel_reset(panel);
        xl9555_->SetOutputState(8, 1);
        xl9555_->SetOutputState(2, 0);

        esp_lcd_panel_init(panel);
        esp_lcd_panel_invert_color(panel, DISPLAY_BACKLIGHT_OUTPUT_INVERT);
        esp_lcd_panel_swap_xy(panel, DISPLAY_SWAP_XY); 
        esp_lcd_panel_mirror(panel, DISPLAY_MIRROR_X, DISPLAY_MIRROR_Y);
        display_ = new SpiLcdDisplay(panel_io, panel,
                                    DISPLAY_WIDTH, DISPLAY_HEIGHT, DISPLAY_OFFSET_X, DISPLAY_OFFSET_Y, DISPLAY_MIRROR_X, DISPLAY_MIRROR_Y, DISPLAY_SWAP_XY);
    }

    // 初始化摄像头：ov2640；
    // 根据正点原子官方示例参数
    void InitializeCamera() {
#if ENABLE_CAMERA_FEATURE
        ESP_LOGI(TAG, "初始化相机功能...");
        
        xl9555_->SetOutputState(OV_PWDN_IO, 0); // PWDN=低 (上电)
        vTaskDelay(pdMS_TO_TICKS(100));          // 延长上电延时
        xl9555_->SetOutputState(OV_RESET_IO, 0); // 确保复位
        vTaskDelay(pdMS_TO_TICKS(100));          // 延长复位保持时间
        xl9555_->SetOutputState(OV_RESET_IO, 1); // 释放复位
        vTaskDelay(pdMS_TO_TICKS(200));          // 延长复位释放时间

        camera_config_t config = {};

        config.pin_pwdn = CAM_PIN_PWDN;  // 实际由 XL9555 控制
        config.pin_reset = CAM_PIN_RESET;// 实际由 XL9555 控制
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

        /* XCLK 10MHz for OV2640 - 降低时钟频率提高稳定性 */
        config.xclk_freq_hz = 10000000;
        config.ledc_timer = LEDC_TIMER_0;
        config.ledc_channel = LEDC_CHANNEL_0;

        config.pixel_format = PIXFORMAT_RGB565;   /* YUV422,GRAYSCALE,RGB565,JPEG */
        config.frame_size = FRAMESIZE_QVGA;       /* QQVGA-UXGA, For ESP32, do not use sizes above QVGA when not JPEG. The performance of the ESP32-S series has improved a lot, but JPEG mode always gives better frame rates */

        config.jpeg_quality = 12;                 /* 0-63, for OV series camera sensors, lower number means higher quality */
        config.fb_count = 1;                      /* 减少缓冲区，提高稳定性 */
        config.fb_location = CAMERA_FB_IN_PSRAM;
        config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;

        esp_err_t err = esp_camera_init(&config); // 测试相机是否存在
        if (err != ESP_OK) {
            ESP_LOGE(TAG, "Camera is not plugged in or not supported, error: %s", esp_err_to_name(err));
            // 如果摄像头初始化失败，设置 camera_ 为 nullptr
            camera_ = nullptr;
            return;
        }else
        {
            esp_camera_deinit();// 释放之前的摄像头资源,为正确初始化做准备
            camera_ = new Esp32Camera(config);
            ESP_LOGI(TAG, "相机功能初始化完成");
        }
#else
        ESP_LOGI(TAG, "相机功能已禁用");
        camera_ = nullptr;
#endif
    }

    void InitializeGimbal() {
        ESP_LOGI(TAG, "初始化云台...");
        
        // 初始化云台 - 水平舵机GPIO19 (0-270度), 垂直舵机GPIO20 (0-180度)
        if (Gimbal_init(&gimbal_, SERVO_PAN_GPIO, SERVO_TILT_GPIO) != ESP_OK) {
            ESP_LOGE(TAG, "云台初始化失败!");
            return;
        }
        
        // 设置初始位置
        Gimbal_setAngles(&gimbal_, 135, 90); // 水平舵机135度(中间), 垂直舵机90度(中间)
        
        ESP_LOGI(TAG, "云台初始化完成 - PAN: GPIO%d (0-270°), TILT: GPIO%d (0-180°)", 
                 SERVO_PAN_GPIO, SERVO_TILT_GPIO);
    }

    void InitializeCan() {
#if ENABLE_CAN_FEATURE
        ESP_LOGI(TAG, "初始化CAN总线...TX=%d, RX=%d", CAN_TX_GPIO, CAN_RX_GPIO);
        
        // 创建深度电机管理器（集成LED功能）
        deep_motor_ = new DeepMotor(led_strip_);
        
        // 创建机械臂控制器（假设6个电机ID为1-6）
        uint8_t motor_ids[6] = {1, 2, 3, 4, 5, 6};
        deep_arm_ = new DeepArm(deep_motor_, motor_ids);
        
        // 初始化CAN总线
        if (ESP32Can.begin(ESP32Can.convertSpeed(1000), CAN_TX_GPIO, CAN_RX_GPIO, 10, 10)) {
            ESP_LOGI(TAG, "CAN总线启动成功! TX=%d, RX=%d, 速度=1000kbps", CAN_TX_GPIO, CAN_RX_GPIO);
            
            // 创建CAN接收任务
            BaseType_t ret = xTaskCreate(can_receive_task, "can_receive", 4096, this, 5, &can_receive_task_handle_);
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
        deep_motor_ = nullptr;
        deep_arm_ = nullptr;
#endif
    }

    void InitializeWs2812() {
#if ENABLE_LED_STRIP_FEATURE
        ESP_LOGI(TAG, "初始化2812灯带...GPIO=%d, LED数量=%d", WS2812_STRIP_GPIO, WS2812_LED_COUNT);
        
        led_strip_ = new CircularStrip(WS2812_STRIP_GPIO, WS2812_LED_COUNT);
#else
        ESP_LOGI(TAG, "2812灯带功能已禁用");
        led_strip_ = nullptr;
#endif
    }
    
    void InitializeControls() {
        auto& mcp_server = McpServer::GetInstance();
        (void)mcp_server; // 避免未使用变量警告
        
        // 初始化各个控制类
#if ENABLE_LED_STRIP_FEATURE
        led_control_ = new LedStripControl(led_strip_, mcp_server);
        ESP_LOGI(TAG, "LED灯带控制类初始化完成");
#else
        led_control_ = nullptr;
#endif

#if ENABLE_CAN_FEATURE
        deep_motor_control_ = new DeepMotorControl(deep_motor_, mcp_server); // 电机控制（LED已集成到DeepMotor中）
        ESP_LOGI(TAG, "电机控制类初始化完成");
        
        // 启动机械臂状态更新任务
        // BaseType_t ret = xTaskCreate(arm_status_update_task, "arm_status_update", 2048, this, 3, &arm_status_update_task_handle_);
        // if (ret != pdPASS) {
        //     ESP_LOGE(TAG, "创建机械臂状态更新任务失败!");
        // } else {
        //     ESP_LOGI(TAG, "机械臂状态更新任务创建成功!");
        // }
#else
        deep_motor_control_ = nullptr;
#endif

        
        // gimbal_control_ = new GimbalControl(&gimbal_, mcp_server);         // 临时屏蔽舵机控制
        // deep_arm_control_ = new DeepArmControl(deep_arm_, mcp_server, led_strip_);        // 机械臂MCP控制
        
        // 初始化MJPEG服务器
#if ENABLE_CAMERA_FEATURE
        InitializeMjpegServer();
#endif
        
        ESP_LOGI(TAG, "控制类初始化完成");
    }
    
    void InitializeMjpegServer() {
        if (camera_ == nullptr) {
            ESP_LOGI(TAG, "相机未初始化，跳过MJPEG服务器");
            return;
        }
        
        // 创建MJPEG服务器（不立即启动）
        mjpeg_server_ = std::make_unique<MjpegServer>(8080);  // 端口8080
        mjpeg_server_->SetFrameRate(10);   // 10fps
        mjpeg_server_->SetJpegQuality(80); // JPEG质量80
        
        ESP_LOGI(TAG, "MJPEG服务器对象创建完成");
        ESP_LOGI(TAG, "等待WiFi连接后自动启动服务器...");
        
        ESP_LOGI(TAG, "MJPEG服务器初始化完成");
    }
    
    void StartMjpegServerWhenReady() {
        if (mjpeg_server_ == nullptr) {
            ESP_LOGW(TAG, "MJPEG服务器对象未创建");
            return;
        }
        
        if (mjpeg_server_->IsRunning()) {
            ESP_LOGI(TAG, "MJPEG服务器已在运行");
            return;
        }
        
        ESP_LOGI(TAG, "WiFi已连接，启动MJPEG服务器...");
        
        // 延迟一下，确保网络栈完全就绪
        vTaskDelay(pdMS_TO_TICKS(2000));
        
        if (mjpeg_server_->Start()) {
            ESP_LOGI(TAG, "MJPEG服务器启动成功");
            ESP_LOGI(TAG, "访问地址: %s", mjpeg_server_->GetUrl().c_str());
            ESP_LOGI(TAG, "可通过VLC、浏览器或ffmpeg直接访问视频流");
        } else {
            ESP_LOGE(TAG, "MJPEG服务器启动失败");
        }
    }
    
    // 机械臂状态更新任务
    static void arm_status_update_task(void *pvParameters) {
        atk_dnesp32s3* board = static_cast<atk_dnesp32s3*>(pvParameters);
        (void)board; // 避免未使用变量警告
        
        while (1) {
            // if (board->deep_arm_control_) {
            //     board->deep_arm_control_->UpdateArmStatus();
            // }
            vTaskDelay(pdMS_TO_TICKS(500)); // 每500ms更新一次状态
        }
    }

    // CAN接收任务
    static void can_receive_task(void *pvParameters) {
        atk_dnesp32s3* board = static_cast<atk_dnesp32s3*>(pvParameters);
        CanFrame rxFrame;
        
        ESP_LOGI(TAG, "CAN接收任务启动");
        
        while(1) {
            if(ESP32Can.readFrame(rxFrame, 1000)) {
                // if(rxFrame.extd) {
                //     ESP_LOGI(TAG, "接收到扩展帧: ID=0x%08lX, 长度=%d, 数据=[", 
                //            rxFrame.identifier, rxFrame.data_length_code);
                // } else {
                //     ESP_LOGI(TAG, "接收到标准帧: ID=0x%03lX, 长度=%d, 数据=[", 
                //            rxFrame.identifier, rxFrame.data_length_code);
                // }
                
                // for(int i = 0; i < rxFrame.data_length_code; i++) {
                //     ESP_LOGI(TAG, "%02X", rxFrame.data[i]);
                //     if(i < rxFrame.data_length_code - 1) ESP_LOGI(TAG, " ");
                // }
                // ESP_LOGI(TAG, "]");
                
                // 处理电机反馈帧（通过DeepMotor）
                if (board->deep_motor_ && board->deep_motor_->processCanFrame(rxFrame)) {
                    // 电机反馈帧已由DeepMotor处理
                }
                // 处理舵机控制指令
                else if(rxFrame.identifier == CAN_CMD_SERVO_CONTROL) {
                    Gimbal_handleCanCommand(&board->gimbal_, &rxFrame);
                }
            }
            
            vTaskDelay(10 / portTICK_PERIOD_MS); // 10ms延迟
        }
    }

        
        


public:
    atk_dnesp32s3() : boot_button_(BOOT_BUTTON_GPIO, false), can_receive_task_handle_(nullptr), arm_status_update_task_handle_(nullptr), deep_motor_(nullptr), deep_arm_(nullptr), led_strip_(nullptr) {
        InitializeI2c();
        InitializeSpi();
        InitializeSt7789Display();
        InitializeButtons();
        InitializeCamera();
        InitializeGimbal();
        
#if ENABLE_CAN_FEATURE || ENABLE_LED_STRIP_FEATURE
        InitializeWs2812();  // 先初始化2812灯带（DeepMotor需要使用）
        InitializeCan();     // 再初始化CAN和DeepMotor（使用led_strip_）
#endif
        InitializeControls(); // 最后初始化所有控制类
    }

    ~atk_dnesp32s3() {
        // 删除CAN接收任务
        if (can_receive_task_handle_ != nullptr) {
            vTaskDelete(can_receive_task_handle_);
        }
        // 删除机械臂状态更新任务
        if (arm_status_update_task_handle_ != nullptr) {
            vTaskDelete(arm_status_update_task_handle_);
        }
        
        // 删除控制类
        if (led_control_ != nullptr) {
            delete led_control_;
        }
        if (deep_motor_control_ != nullptr) {
            delete deep_motor_control_;
        }
        // if (gimbal_control_ != nullptr) {
        //     delete gimbal_control_;
        // }
        // if (deep_arm_control_ != nullptr) {
        //     delete deep_arm_control_;
        // }
        
        // 删除机械臂控制器
        if (deep_arm_ != nullptr) {
            delete deep_arm_;
        }
        // 删除深度电机管理器
        if (deep_motor_ != nullptr) {
            delete deep_motor_;
        }
        // 删除2812灯带
        if (led_strip_ != nullptr) {
            delete led_strip_;
        }
        Gimbal_deinit(&gimbal_);
    }

    virtual Led* GetLed() override {
        static SingleLed led(BUILTIN_LED_GPIO);
        return &led;
    }

    virtual void StartNetwork() override {
        // 注册WiFi事件处理器，在连接成功后启动MJPEG服务器
        esp_event_handler_register(WIFI_EVENT, WIFI_EVENT_STA_CONNECTED,
            [](void* arg, esp_event_base_t event_base, int32_t event_id, void* event_data) {
                auto* board = static_cast<atk_dnesp32s3*>(arg);
                // 创建一个延迟任务来启动MJPEG服务器
                xTaskCreate(
                    [](void* pvParameters) {
                        auto* board = static_cast<atk_dnesp32s3*>(pvParameters);
                        board->StartMjpegServerWhenReady();
                        vTaskDelete(NULL);
                    },
                    "mjpeg_starter",
                    8192,  // 8KB栈空间
                    board,
                    5,
                    nullptr
                );
            },
            this
        );
        
        // 调用父类的网络启动方法
        WifiBoard::StartNetwork();
    }

    virtual AudioCodec* GetAudioCodec() override {
        static Es8388AudioCodec audio_codec(
            i2c_bus_, 
            I2C_NUM_0, 
            AUDIO_INPUT_SAMPLE_RATE, 
            AUDIO_OUTPUT_SAMPLE_RATE,
            AUDIO_I2S_GPIO_MCLK, 
            AUDIO_I2S_GPIO_BCLK, 
            AUDIO_I2S_GPIO_WS, 
            AUDIO_I2S_GPIO_DOUT, 
            AUDIO_I2S_GPIO_DIN,
            GPIO_NUM_NC, 
            AUDIO_CODEC_ES8388_ADDR
        );
        return &audio_codec;
    }

    virtual Display* GetDisplay() override {
        return display_;
    }
    
    virtual Camera* GetCamera() override {
        return camera_;
    }
};

DECLARE_BOARD(atk_dnesp32s3);
