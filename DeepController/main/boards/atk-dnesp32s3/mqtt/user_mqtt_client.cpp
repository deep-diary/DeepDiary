#include "user_mqtt_client.h"
#include "board.h"
#include "application.h"
#include "wifi_station.h"
#include <esp_system.h>
#include <esp_mac.h>
#include <cstring>
#include <sstream>
#include <iomanip>

UserMqttClient::UserMqttClient() 
    : connected_(false), initialized_(false), retry_count_(0), last_heartbeat_time_(0) {
    
    // 创建事件组
    event_group_ = xEventGroupCreate();
    if (event_group_ == nullptr) {
        ESP_LOGE(TAG_USER_MQTT, "Failed to create event group");
        return;
    }
    
    // 创建心跳定时器
    esp_timer_create_args_t heartbeat_timer_args = {
        .callback = HeartbeatTimerCallback,
        .arg = this,
        .name = "user_mqtt_heartbeat"
    };
    esp_timer_create(&heartbeat_timer_args, &heartbeat_timer_);
    
    // 创建重连定时器
    esp_timer_create_args_t reconnect_timer_args = {
        .callback = ReconnectTimerCallback,
        .arg = this,
        .name = "user_mqtt_reconnect"
    };
    esp_timer_create(&reconnect_timer_args, &reconnect_timer_);
    
    ESP_LOGI(TAG_USER_MQTT, "UserMqttClient initialized");
}

UserMqttClient::~UserMqttClient() {
    Disconnect();
    
    if (heartbeat_timer_) {
        esp_timer_stop(heartbeat_timer_);
        esp_timer_delete(heartbeat_timer_);
    }
    
    if (reconnect_timer_) {
        esp_timer_stop(reconnect_timer_);
        esp_timer_delete(reconnect_timer_);
    }
    
    if (event_group_) {
        vEventGroupDelete(event_group_);
    }
    
    ESP_LOGI(TAG_USER_MQTT, "UserMqttClient destroyed");
}

bool UserMqttClient::Initialize(const UserMqttClientConfig& config) {
    config_ = config;
    initialized_ = true;
    
    ESP_LOGI(TAG_USER_MQTT, "Initialized with broker: %s:%d, client_id: %s", 
             config_.broker_host.c_str(), config_.broker_port, config_.client_id.c_str());
    
    return true;
}

bool UserMqttClient::Connect() {
    if (!initialized_) {
        last_error_ = "Not initialized";
        ESP_LOGE(TAG_USER_MQTT, "Client not initialized");
        return false;
    }
    
    if (connected_) {
        ESP_LOGW(TAG_USER_MQTT, "Already connected");
        return true;
    }
    
    if (!CreateMqttClient()) {
        return false;
    }
    
    SetupCallbacks();
    
    ESP_LOGI(TAG_USER_MQTT, "Connecting to broker %s:%d", 
             config_.broker_host.c_str(), config_.broker_port);
    
    // 连接到MQTT broker
    if (!mqtt_client_->Connect(config_.broker_host, config_.broker_port, 
                              config_.client_id, config_.username, config_.password)) {
        last_error_ = "Failed to connect to broker";
        ESP_LOGE(TAG_USER_MQTT, "Failed to connect to broker");
        return false;
    }
    
    // 等待连接结果
    EventBits_t bits = xEventGroupWaitBits(event_group_, 
                                          MQTT_CONNECTED_BIT | MQTT_ERROR_BIT,
                                          pdTRUE, pdFALSE, 
                                          pdMS_TO_TICKS(MQTT_CONNECT_TIMEOUT_MS));
    
    if (bits & MQTT_CONNECTED_BIT) {
        connected_ = true;
        retry_count_ = 0;
        ESP_LOGI(TAG_USER_MQTT, "Successfully connected to broker");
        
        // 等待 MQTT 客户端完全就绪
        vTaskDelay(pdMS_TO_TICKS(500));
        
        // 订阅控制主题
        if (!config_.control_topic.empty()) {
            ESP_LOGI(TAG_USER_MQTT, "📡 SUBSCRIBING to Control Topic");
            ESP_LOGI(TAG_USER_MQTT, "  Topic: %s", config_.control_topic.c_str());
            
            // 检查客户端是否真的可用
            if (!mqtt_client_) {
                ESP_LOGE(TAG_USER_MQTT, "  ❌ MQTT client is null");
            } else if (!mqtt_client_->IsConnected()) {
                ESP_LOGE(TAG_USER_MQTT, "  ❌ MQTT client is not connected");
            } else {
                if (mqtt_client_->Subscribe(config_.control_topic)) {
                    ESP_LOGI(TAG_USER_MQTT, "  ✅ Subscription successful");
                } else {
                    ESP_LOGE(TAG_USER_MQTT, "  ❌ Subscription failed");
                }
            }
        } else {
            ESP_LOGW(TAG_USER_MQTT, "⚠️ No control topic configured, skipping subscription");
        }
        
        // 启动心跳定时器
        esp_timer_start_periodic(heartbeat_timer_, HEARTBEAT_INTERVAL_MS * 1000);
        
        // 发送连接成功状态
        SendStatus("connected", "Successfully connected to user MQTT broker");
        
        if (connection_callback_) {
            connection_callback_(true);
        }
        
        return true;
    } else {
        connected_ = false;
        retry_count_++;
        last_error_ = "Connection timeout";
        ESP_LOGE(TAG_USER_MQTT, "Connection timeout");
        
        if (connection_callback_) {
            connection_callback_(false);
        }
        
        return false;
    }
}

void UserMqttClient::Disconnect() {
    if (!connected_) {
        return;
    }
    
    connected_ = false;
    
    // 停止定时器
    if (heartbeat_timer_) {
        esp_timer_stop(heartbeat_timer_);
    }
    if (reconnect_timer_) {
        esp_timer_stop(reconnect_timer_);
    }
    
    // 发送断开连接状态
    SendStatus("disconnected", "Disconnected from user MQTT broker");
    
    // 断开MQTT连接
    if (mqtt_client_) {
        mqtt_client_.reset();
    }
    
    ESP_LOGI(TAG_USER_MQTT, "Disconnected from broker");
    
    if (connection_callback_) {
        connection_callback_(false);
    }
}

bool UserMqttClient::IsConnected() const {
    return connected_ && mqtt_client_ != nullptr;
}

bool UserMqttClient::SendStatus(const std::string& status, const std::string& message) {
    if (!IsConnected()) {
        return false;
    }
    
    std::string json = StatusToJson(status, message);
    if (json.empty()) {
        return false;
    }
    
    if (!mqtt_client_->Publish(config_.status_topic, json)) {
        ESP_LOGE(TAG_USER_MQTT, "Failed to publish status");
        return false;
    }
    
    ESP_LOGI(TAG_USER_MQTT, "📤 PUBLISH Status");
    ESP_LOGI(TAG_USER_MQTT, "  Topic: %s", config_.status_topic.c_str());
    ESP_LOGI(TAG_USER_MQTT, "  Status: %s", status.c_str());
    ESP_LOGI(TAG_USER_MQTT, "  Message: %s", message.c_str());
    ESP_LOGI(TAG_USER_MQTT, "  Payload: %s", json.c_str());
    return true;
}

bool UserMqttClient::SendHeartbeat() {
    if (!IsConnected()) {
        return false;
    }
    
    last_heartbeat_time_ = esp_timer_get_time() / 1000000; // 转换为秒
    
    cJSON* root = cJSON_CreateObject();
    cJSON_AddStringToObject(root, "type", "heartbeat");
    cJSON_AddNumberToObject(root, "timestamp", last_heartbeat_time_);
    cJSON_AddStringToObject(root, "device_id", config_.client_id.c_str());
    
    char* json_string = cJSON_PrintUnformatted(root);
    std::string json(json_string);
    cJSON_free(json_string);
    cJSON_Delete(root);
    
    if (!mqtt_client_->Publish(config_.status_topic, json)) {
        ESP_LOGE(TAG_USER_MQTT, "Failed to publish heartbeat");
        return false;
    }
    
    ESP_LOGI(TAG_USER_MQTT, "💓 PUBLISH Heartbeat");
    ESP_LOGI(TAG_USER_MQTT, "  Topic: %s", config_.status_topic.c_str());
    ESP_LOGI(TAG_USER_MQTT, "  Payload: %s", json.c_str());
    return true;
}

bool UserMqttClient::SendDeviceConfig(const DeviceConfigInfo& config) {
    if (!IsConnected()) {
        ESP_LOGW(TAG_USER_MQTT, "Not connected, cannot send device config");
        return false;
    }
    
    cJSON* root = cJSON_CreateObject();
    cJSON_AddStringToObject(root, "device_id", config.device_id.c_str());
    cJSON_AddStringToObject(root, "device_type", config.device_type.c_str());
    cJSON_AddStringToObject(root, "firmware_version", config.firmware_version.c_str());
    cJSON_AddStringToObject(root, "mac_address", config.mac_address.c_str());
    cJSON_AddStringToObject(root, "chip_model", config.chip_model.c_str());
    cJSON_AddStringToObject(root, "chip_revision", config.chip_revision.c_str());
    
    // 硬件能力
    cJSON* capabilities = cJSON_CreateObject();
    cJSON_AddBoolToObject(capabilities, "camera", config.capabilities.camera);
    cJSON_AddBoolToObject(capabilities, "can_bus", config.capabilities.can_bus);
    cJSON_AddBoolToObject(capabilities, "led_strip", config.capabilities.led_strip);
    cJSON_AddBoolToObject(capabilities, "gimbal", config.capabilities.gimbal);
    cJSON_AddBoolToObject(capabilities, "arm", config.capabilities.arm);
    cJSON_AddBoolToObject(capabilities, "motor", config.capabilities.motor);
    cJSON_AddBoolToObject(capabilities, "sensor", config.capabilities.sensor);
    cJSON_AddItemToObject(root, "hardware_capabilities", capabilities);
    
    char* json_string = cJSON_PrintUnformatted(root);
    std::string json(json_string);
    cJSON_free(json_string);
    cJSON_Delete(root);
    
    if (!mqtt_client_->Publish(config_.device_info_topic, json)) {
        ESP_LOGE(TAG_USER_MQTT, "Failed to publish device info");
        return false;
    }
    
    ESP_LOGI(TAG_USER_MQTT, "📤 PUBLISH Device Info");
    ESP_LOGI(TAG_USER_MQTT, "  Topic: %s", config_.device_info_topic.c_str());
    ESP_LOGI(TAG_USER_MQTT, "  Payload: %s", json.c_str());
    return true;
}

bool UserMqttClient::SendSystemStatus(const DeviceStatus::SystemInfo& system_info) {
    if (!IsConnected()) {
        return false;
    }
    
    cJSON* root = cJSON_CreateObject();
    cJSON_AddStringToObject(root, "wifi_ssid", system_info.wifi_ssid.c_str());
    cJSON_AddStringToObject(root, "ip_address", system_info.ip_address.c_str());
    cJSON_AddNumberToObject(root, "free_heap", system_info.free_heap);
    cJSON_AddNumberToObject(root, "uptime_seconds", system_info.uptime_seconds);
    cJSON_AddNumberToObject(root, "cpu_temperature", system_info.cpu_temperature);
    cJSON_AddStringToObject(root, "network_status", system_info.network_status.c_str());
    cJSON_AddNumberToObject(root, "timestamp", esp_timer_get_time() / 1000000);
    
    char* json_string = cJSON_PrintUnformatted(root);
    std::string json(json_string);
    cJSON_free(json_string);
    cJSON_Delete(root);
    
    if (!mqtt_client_->Publish(config_.system_status_topic, json)) {
        ESP_LOGE(TAG_USER_MQTT, "Failed to publish system status");
        return false;
    }
    
    ESP_LOGI(TAG_USER_MQTT, "📤 PUBLISH System Status");
    ESP_LOGI(TAG_USER_MQTT, "  Topic: %s", config_.system_status_topic.c_str());
    return true;
}

bool UserMqttClient::SendSensorStatus(const DeviceStatus::SensorData& sensor_data) {
    if (!IsConnected()) {
        return false;
    }
    
    cJSON* root = cJSON_CreateObject();
    cJSON_AddNumberToObject(root, "acc_x", sensor_data.acc_x);
    cJSON_AddNumberToObject(root, "acc_y", sensor_data.acc_y);
    cJSON_AddNumberToObject(root, "acc_z", sensor_data.acc_z);
    cJSON_AddNumberToObject(root, "acc_g", sensor_data.acc_g);
    cJSON_AddNumberToObject(root, "pitch", sensor_data.pitch);
    cJSON_AddNumberToObject(root, "roll", sensor_data.roll);
    cJSON_AddStringToObject(root, "sensor_status", sensor_data.sensor_status.c_str());
    cJSON_AddNumberToObject(root, "timestamp", esp_timer_get_time() / 1000000);
    
    char* json_string = cJSON_PrintUnformatted(root);
    std::string json(json_string);
    cJSON_free(json_string);
    cJSON_Delete(root);
    
    if (!mqtt_client_->Publish(config_.sensor_status_topic, json)) {
        ESP_LOGE(TAG_USER_MQTT, "Failed to publish sensor status");
        return false;
    }
    
    ESP_LOGI(TAG_USER_MQTT, "📤 PUBLISH Sensor Status");
    ESP_LOGI(TAG_USER_MQTT, "  Topic: %s", config_.sensor_status_topic.c_str());
    return true;
}

bool UserMqttClient::SendActuatorStatus(const DeviceStatus::ActuatorStatus& actuator_status) {
    if (!IsConnected()) {
        return false;
    }
    
    cJSON* root = cJSON_CreateObject();
    
    // 机械臂状态
    cJSON* arm = cJSON_CreateObject();
    cJSON_AddBoolToObject(arm, "connected", actuator_status.arm.connected);
    cJSON_AddNumberToObject(arm, "motor_count", actuator_status.arm.motor_count);
    cJSON_AddStringToObject(arm, "status", actuator_status.arm.status.c_str());
    cJSON_AddItemToObject(root, "arm", arm);
    
    // 电机状态
    cJSON* motor = cJSON_CreateObject();
    cJSON_AddBoolToObject(motor, "connected", actuator_status.motor.connected);
    cJSON_AddNumberToObject(motor, "motor_count", actuator_status.motor.motor_count);
    cJSON_AddStringToObject(motor, "status", actuator_status.motor.status.c_str());
    cJSON_AddItemToObject(root, "motor", motor);
    
    cJSON_AddNumberToObject(root, "timestamp", esp_timer_get_time() / 1000000);
    
    char* json_string = cJSON_PrintUnformatted(root);
    std::string json(json_string);
    cJSON_free(json_string);
    cJSON_Delete(root);
    
    if (!mqtt_client_->Publish(config_.actuator_status_topic, json)) {
        ESP_LOGE(TAG_USER_MQTT, "Failed to publish actuator status");
        return false;
    }
    
    ESP_LOGI(TAG_USER_MQTT, "📤 PUBLISH Actuator Status");
    ESP_LOGI(TAG_USER_MQTT, "  Topic: %s", config_.actuator_status_topic.c_str());
    return true;
}

void UserMqttClient::SetControlCallback(std::function<void(const RemoteControlCommand&)> callback) {
    control_callback_ = callback;
}

void UserMqttClient::SetConnectionCallback(std::function<void(bool)> callback) {
    connection_callback_ = callback;
}

void UserMqttClient::UpdateConfig(const UserMqttClientConfig& config) {
    config_ = config;
    ESP_LOGI(TAG_USER_MQTT, "Configuration updated");
}

UserMqttClientConfig UserMqttClient::GetConfig() const {
    return config_;
}

std::string UserMqttClient::GetLastError() const {
    return last_error_;
}

int UserMqttClient::GetConnectionRetryCount() const {
    return retry_count_;
}

bool UserMqttClient::CreateMqttClient() {
    auto network = Board::GetInstance().GetNetwork();
    if (!network) {
        last_error_ = "Network not available";
        ESP_LOGE(TAG_USER_MQTT, "Network not available");
        return false;
    }
    
    // 使用连接ID 1，避免与主MQTT连接冲突
    mqtt_client_ = network->CreateMqtt(1);
    if (!mqtt_client_) {
        last_error_ = "Failed to create MQTT client";
        ESP_LOGE(TAG_USER_MQTT, "Failed to create MQTT client");
        return false;
    }
    
    mqtt_client_->SetKeepAlive(config_.keepalive_interval);
    return true;
}

void UserMqttClient::SetupCallbacks() {
    mqtt_client_->OnConnected([this]() {
        OnConnected();
    });
    
    mqtt_client_->OnDisconnected([this]() {
        OnDisconnected();
    });
    
    mqtt_client_->OnMessage([this](const std::string& topic, const std::string& payload) {
        OnMessage(topic, payload);
    });
}

void UserMqttClient::OnConnected() {
    ESP_LOGI(TAG_USER_MQTT, "🔗 MQTT CONNECTED");
    ESP_LOGI(TAG_USER_MQTT, "  Broker: %s:%d", config_.broker_host.c_str(), config_.broker_port);
    ESP_LOGI(TAG_USER_MQTT, "  Client ID: %s", config_.client_id.c_str());
    ESP_LOGI(TAG_USER_MQTT, "  Device Info Topic: %s", config_.device_info_topic.c_str());
    ESP_LOGI(TAG_USER_MQTT, "  Control Topic: %s", config_.control_topic.c_str());
    ESP_LOGI(TAG_USER_MQTT, "  Status Topic: %s", config_.status_topic.c_str());
    
    connected_ = true;  // 设置连接状态
    retry_count_ = 0;   // 重置重试计数
    
    xEventGroupSetBits(event_group_, MQTT_CONNECTED_BIT);
}

void UserMqttClient::OnDisconnected() {
    ESP_LOGI(TAG_USER_MQTT, "MQTT disconnected");
    connected_ = false;
    xEventGroupSetBits(event_group_, MQTT_DISCONNECTED_BIT);
    
    // 启动重连定时器
    if (retry_count_ < MAX_RETRY_COUNT) {
        esp_timer_start_once(reconnect_timer_, MQTT_RECONNECT_INTERVAL_MS * 1000);
    }
}

void UserMqttClient::OnMessage(const std::string& topic, const std::string& payload) {
    ESP_LOGI(TAG_USER_MQTT, "📥 RECEIVE Message");
    ESP_LOGI(TAG_USER_MQTT, "  Topic: %s", topic.c_str());
    ESP_LOGI(TAG_USER_MQTT, "  Payload: %s", payload.c_str());
    
    if (topic == config_.control_topic) {
        ESP_LOGI(TAG_USER_MQTT, "  → Processing as control command");
        ParseControlMessage(topic, payload);
    } else {
        ESP_LOGW(TAG_USER_MQTT, "  → Unknown topic, ignoring");
    }
}

void UserMqttClient::ParseControlMessage(const std::string& topic, const std::string& payload) {
    ESP_LOGI(TAG_USER_MQTT, "🔧 PARSING Control Command");
    
    cJSON* root = cJSON_Parse(payload.c_str());
    if (!root) {
        ESP_LOGE(TAG_USER_MQTT, "  ❌ Failed to parse control message JSON");
        return;
    }
    
    RemoteControlCommand command = ParseCommand(root);
    cJSON_Delete(root);
    
    if (!command.command_type.empty() && control_callback_) {
        ESP_LOGI(TAG_USER_MQTT, "  ✅ Command parsed successfully:");
        ESP_LOGI(TAG_USER_MQTT, "    Type: %s", command.command_type.c_str());
        ESP_LOGI(TAG_USER_MQTT, "    Target: %s", command.target.c_str());
        ESP_LOGI(TAG_USER_MQTT, "    Action: %s", command.action.c_str());
        ESP_LOGI(TAG_USER_MQTT, "  → Executing control command");
        control_callback_(command);
    } else {
        ESP_LOGW(TAG_USER_MQTT, "  ⚠️ Invalid command or no callback set");
    }
}

RemoteControlCommand UserMqttClient::ParseCommand(const cJSON* json) {
    RemoteControlCommand command;
    
    cJSON* type = cJSON_GetObjectItem(json, "type");
    if (cJSON_IsString(type)) {
        command.command_type = type->valuestring;
    }
    
    cJSON* target = cJSON_GetObjectItem(json, "target");
    if (cJSON_IsString(target)) {
        command.target = target->valuestring;
    }
    
    cJSON* action = cJSON_GetObjectItem(json, "action");
    if (cJSON_IsString(action)) {
        command.action = action->valuestring;
    }
    
    cJSON* params = cJSON_GetObjectItem(json, "parameters");
    if (cJSON_IsObject(params)) {
        command.parameters = cJSON_Duplicate(params, 1);
    }
    
    return command;
}

std::string UserMqttClient::StatusToJson(const std::string& status, const std::string& message) {
    cJSON* root = cJSON_CreateObject();
    
    cJSON_AddStringToObject(root, "type", "status");
    cJSON_AddStringToObject(root, "status", status.c_str());
    cJSON_AddStringToObject(root, "message", message.c_str());
    cJSON_AddNumberToObject(root, "timestamp", esp_timer_get_time() / 1000000);
    cJSON_AddStringToObject(root, "device_id", config_.client_id.c_str());
    
    char* json_string = cJSON_PrintUnformatted(root);
    std::string result(json_string);
    cJSON_free(json_string);
    cJSON_Delete(root);
    
    return result;
}

void UserMqttClient::HeartbeatTimerCallback(void* arg) {
    UserMqttClient* client = static_cast<UserMqttClient*>(arg);
    client->SendHeartbeat();
}

void UserMqttClient::ReconnectTimerCallback(void* arg) {
    UserMqttClient* client = static_cast<UserMqttClient*>(arg);
    ESP_LOGI(TAG_USER_MQTT, "Attempting to reconnect...");
    client->Connect();
}

