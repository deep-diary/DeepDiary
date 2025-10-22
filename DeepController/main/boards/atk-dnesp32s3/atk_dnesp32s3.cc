/**
 * @file atk_dnesp32s3_minimal.cc
 * @brief ATK-DNESP32S3 板级主文件（简化版）
 * 
 * 本文件尽可能保持与开源项目原始代码一致，所有自定义的新增功能
 * 都通过 BoardExtensions 类管理，便于后续升级开源项目代码。
 * 
 * 对比原始文件的修改：
 * 1. 新增 board_extensions.h 头文件
 * 2. 添加 extensions_ 成员变量
 * 3. 在构造函数中创建扩展对象
 * 4. 在 StartNetwork() 中添加 MJPEG 服务器启动
 * 5. 在 GetCamera() 中返回扩展对象的摄像头
 */

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

// ========== 新增：板级扩展功能 ==========
#include "board_extensions.h"

#include <esp_log.h>
#include <esp_lcd_panel_vendor.h>
#include <esp_event.h>
#include <esp_wifi.h>
#include <driver/i2c_master.h>
#include <driver/spi_common.h>
#include <wifi_station.h>
#include <cJSON.h>

#define TAG "atk_dnesp32s3"

class atk_dnesp32s3 : public WifiBoard {
private:
    i2c_master_bus_handle_t i2c_bus_;
    Button boot_button_;
    LcdDisplay* display_;
    
    // ========== 新增：板级扩展对象 ==========
    BoardExtensions* extensions_;

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
        
        // ========== 修改：通过扩展对象控制XL9555 ==========
        esp_lcd_panel_reset(panel);
        if (extensions_ && extensions_->GetXL9555()) {
            extensions_->GetXL9555()->SetOutputState(8, 1);
            extensions_->GetXL9555()->SetOutputState(2, 0);
        }

        esp_lcd_panel_init(panel);
        esp_lcd_panel_invert_color(panel, DISPLAY_BACKLIGHT_OUTPUT_INVERT);
        esp_lcd_panel_swap_xy(panel, DISPLAY_SWAP_XY); 
        esp_lcd_panel_mirror(panel, DISPLAY_MIRROR_X, DISPLAY_MIRROR_Y);
        display_ = new SpiLcdDisplay(panel_io, panel,
                                    DISPLAY_WIDTH, DISPLAY_HEIGHT, 
                                    DISPLAY_OFFSET_X, DISPLAY_OFFSET_Y, 
                                    DISPLAY_MIRROR_X, DISPLAY_MIRROR_Y, 
                                    DISPLAY_SWAP_XY);
    }

public:
    atk_dnesp32s3() 
        : boot_button_(BOOT_BUTTON_GPIO, false)
        , extensions_(nullptr) {
        
        // 基础硬件初始化（与开源项目保持一致）
        InitializeI2c();
        InitializeSpi();
        
        // ========== 新增：创建扩展对象（必须在显示屏初始化前，因为需要XL9555） ==========
        extensions_ = new BoardExtensions(i2c_bus_, nullptr);
        
        // 初始化显示屏（需要XL9555控制）
        InitializeSt7789Display();
        
        // ========== 重要：将display指针传递给扩展对象 ==========
        if (extensions_) {
            extensions_->SetDisplay(display_);
            ESP_LOGI(TAG, "Display指针已设置到BoardExtensions: %p", display_);
        }
        
        // 初始化按键
        InitializeButtons();
        
        ESP_LOGI(TAG, "板级初始化完成");
    }

    ~atk_dnesp32s3() {
        delete extensions_;
    }

    virtual Led* GetLed() override {
        static SingleLed led(BUILTIN_LED_GPIO);
        return &led;
    }

    // ========== 修改：添加MJPEG服务器启动 ==========
    virtual void StartNetwork() override {
        // 注册WiFi事件处理器
        esp_event_handler_register(WIFI_EVENT, WIFI_EVENT_STA_CONNECTED,
            [](void* arg, esp_event_base_t event_base, int32_t event_id, void* event_data) {
                auto* board = static_cast<atk_dnesp32s3*>(arg);
#if ENABLE_MJPEG_FEATURE
                if (board->extensions_) {
                    // 创建延迟任务启动MJPEG服务器
                    xTaskCreate(
                        [](void* pvParameters) {
                            auto* ext = static_cast<BoardExtensions*>(pvParameters);
                            ext->StartMjpegServerWhenReady();
                            vTaskDelete(NULL);
                        },
                        "mjpeg_starter",
                        8192,
                        board->extensions_,
                        5,
                        nullptr
                    );
                }
#endif
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
    
    // ========== 修改：返回扩展对象的摄像头 ==========
    virtual Camera* GetCamera() override {
        return extensions_ ? extensions_->GetCamera() : nullptr;
    }
};

DECLARE_BOARD(atk_dnesp32s3);

