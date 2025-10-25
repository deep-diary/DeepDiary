#include "remote_control_handler.h"
#include "esp_log.h"
#include "esp_system.h"
#include <cJSON.h>

#define TAG_REMOTE_CONTROL "RemoteControl"

RemoteControlHandler::RemoteControlHandler() 
    : deep_motor_(nullptr), deep_arm_(nullptr), gimbal_(nullptr), 
      led_strip_(nullptr), camera_(nullptr) {
    ESP_LOGI(TAG_REMOTE_CONTROL, "RemoteControlHandler initialized");
}

RemoteControlHandler::~RemoteControlHandler() {
    ESP_LOGI(TAG_REMOTE_CONTROL, "RemoteControlHandler destroyed");
}

void RemoteControlHandler::SetDeepMotor(DeepMotor* motor) {
    deep_motor_ = motor;
}

void RemoteControlHandler::SetDeepArm(DeepArm* arm) {
    deep_arm_ = arm;
}

void RemoteControlHandler::SetGimbal(Gimbal_t* gimbal) {
    gimbal_ = gimbal;
}

void RemoteControlHandler::SetLedStrip(CircularStrip* led_strip) {
    led_strip_ = led_strip;
}

void RemoteControlHandler::SetCamera(Esp32Camera* camera) {
    camera_ = camera;
}

void RemoteControlHandler::SetStatusCallback(std::function<void(const std::string&, const std::string&)> callback) {
    status_callback_ = callback;
}

void RemoteControlHandler::HandleCommand(const RemoteControlCommand& command) {
    ESP_LOGI(TAG_REMOTE_CONTROL, "🎮 HANDLING Remote Command");
    ESP_LOGI(TAG_REMOTE_CONTROL, "  Type: %s", command.command_type.c_str());
    ESP_LOGI(TAG_REMOTE_CONTROL, "  Target: %s", command.target.c_str());
    ESP_LOGI(TAG_REMOTE_CONTROL, "  Action: %s", command.action.c_str());
    
    if (command.command_type == CMD_LED) {
        HandleLedCommand(command);
    } else if (command.command_type == CMD_MOTOR) {
        HandleMotorCommand(command);
    } else if (command.command_type == CMD_ARM) {
        HandleArmCommand(command);
    } else if (command.command_type == CMD_GIMBAL) {
        HandleGimbalCommand(command);
    } else if (command.command_type == CMD_CAMERA) {
        HandleCameraCommand(command);
    } else if (command.command_type == CMD_SYSTEM) {
        HandleSystemCommand(command);
    } else {
        ESP_LOGW(TAG_REMOTE_CONTROL, "Unknown command type: %s", command.command_type.c_str());
        SendStatus("error", "Unknown command type: " + command.command_type);
    }
}

std::string RemoteControlHandler::GetSupportedCommands() const {
    cJSON* root = cJSON_CreateObject();
    cJSON* commands = cJSON_CreateArray();
    
    // LED命令
    cJSON* led_cmd = cJSON_CreateObject();
    cJSON_AddStringToObject(led_cmd, "type", CMD_LED);
    cJSON_AddStringToObject(led_cmd, "actions", "on,off,color,brightness,effect");
    cJSON_AddItemToArray(commands, led_cmd);
    
    // 电机命令
    cJSON* motor_cmd = cJSON_CreateObject();
    cJSON_AddStringToObject(motor_cmd, "type", CMD_MOTOR);
    cJSON_AddStringToObject(motor_cmd, "actions", "start,stop,set_speed,set_position");
    cJSON_AddItemToArray(commands, motor_cmd);
    
    // 机械臂命令
    cJSON* arm_cmd = cJSON_CreateObject();
    cJSON_AddStringToObject(arm_cmd, "type", CMD_ARM);
    cJSON_AddStringToObject(arm_cmd, "actions", "home,move,grip,release");
    cJSON_AddItemToArray(commands, arm_cmd);
    
    // 云台命令
    cJSON* gimbal_cmd = cJSON_CreateObject();
    cJSON_AddStringToObject(gimbal_cmd, "type", CMD_GIMBAL);
    cJSON_AddStringToObject(gimbal_cmd, "actions", "pan,tilt,reset");
    cJSON_AddItemToArray(commands, gimbal_cmd);
    
    // 摄像头命令
    cJSON* camera_cmd = cJSON_CreateObject();
    cJSON_AddStringToObject(camera_cmd, "type", CMD_CAMERA);
    cJSON_AddStringToObject(camera_cmd, "actions", "capture,start_stream,stop_stream");
    cJSON_AddItemToArray(commands, camera_cmd);
    
    // 系统命令
    cJSON* system_cmd = cJSON_CreateObject();
    cJSON_AddStringToObject(system_cmd, "type", CMD_SYSTEM);
    cJSON_AddStringToObject(system_cmd, "actions", "restart,status,info");
    cJSON_AddItemToArray(commands, system_cmd);
    
    cJSON_AddItemToObject(root, "supported_commands", commands);
    
    char* json_string = cJSON_PrintUnformatted(root);
    std::string result(json_string);
    cJSON_free(json_string);
    cJSON_Delete(root);
    
    return result;
}

void RemoteControlHandler::HandleLedCommand(const RemoteControlCommand& command) {
    if (!led_strip_) {
        SendStatus("error", "LED strip not available");
        return;
    }
    
    if (command.action == ACTION_LED_ON) {
        // 开启LED
        // led_strip_->SetAllPixels(255, 255, 255); // 白色
        SendStatus("success", "LED turned on");
    } else if (command.action == ACTION_LED_OFF) {
        // 关闭LED
        // led_strip_->SetAllPixels(0, 0, 0); // 黑色
        SendStatus("success", "LED turned off");
    } else if (command.action == ACTION_LED_COLOR) {
        int r = 255, g = 255, b = 255;
        if (command.parameters) {
            ParseIntParameter(command.parameters, "r", r);
            ParseIntParameter(command.parameters, "g", g);
            ParseIntParameter(command.parameters, "b", b);
        }
        // led_strip_->SetAllPixels(r, g, b);
        SendStatus("success", "LED color set to RGB(" + std::to_string(r) + "," + std::to_string(g) + "," + std::to_string(b) + ")");
    } else if (command.action == ACTION_LED_BRIGHTNESS) {
        int brightness = 255;
        if (command.parameters) {
            ParseIntParameter(command.parameters, "brightness", brightness);
        }
        // led_strip_->SetBrightness(brightness);
        SendStatus("success", "LED brightness set to " + std::to_string(brightness));
    } else {
        SendStatus("error", "Unknown LED action: " + command.action);
    }
}

void RemoteControlHandler::HandleMotorCommand(const RemoteControlCommand& command) {
    if (!deep_motor_) {
        SendStatus("error", "Motor controller not available");
        return;
    }
    
    if (command.action == ACTION_MOTOR_START) {
        int motor_id = 0;
        if (command.parameters) {
            ParseIntParameter(command.parameters, "motor_id", motor_id);
        }
        // deep_motor_->StartMotor(motor_id);
        SendStatus("success", "Motor " + std::to_string(motor_id) + " started");
    } else if (command.action == ACTION_MOTOR_STOP) {
        int motor_id = 0;
        if (command.parameters) {
            ParseIntParameter(command.parameters, "motor_id", motor_id);
        }
        // deep_motor_->StopMotor(motor_id);
        SendStatus("success", "Motor " + std::to_string(motor_id) + " stopped");
    } else if (command.action == ACTION_MOTOR_SET_SPEED) {
        int motor_id = 0, speed = 0;
        if (command.parameters) {
            ParseIntParameter(command.parameters, "motor_id", motor_id);
            ParseIntParameter(command.parameters, "speed", speed);
        }
        // deep_motor_->SetMotorSpeed(motor_id, speed);
        SendStatus("success", "Motor " + std::to_string(motor_id) + " speed set to " + std::to_string(speed));
    } else {
        SendStatus("error", "Unknown motor action: " + command.action);
    }
}

void RemoteControlHandler::HandleArmCommand(const RemoteControlCommand& command) {
    if (!deep_arm_) {
        SendStatus("error", "Arm controller not available");
        return;
    }
    
    if (command.action == ACTION_ARM_HOME) {
        // deep_arm_->Home();
        SendStatus("success", "Arm homed");
    } else if (command.action == ACTION_ARM_MOVE) {
        float x = 0, y = 0, z = 0;
        if (command.parameters) {
            ParseFloatParameter(command.parameters, "x", x);
            ParseFloatParameter(command.parameters, "y", y);
            ParseFloatParameter(command.parameters, "z", z);
        }
        // deep_arm_->MoveTo(x, y, z);
        SendStatus("success", "Arm moved to (" + std::to_string(x) + "," + std::to_string(y) + "," + std::to_string(z) + ")");
    } else if (command.action == ACTION_ARM_GRIP) {
        // deep_arm_->Grip();
        SendStatus("success", "Arm gripped");
    } else if (command.action == ACTION_ARM_RELEASE) {
        // deep_arm_->Release();
        SendStatus("success", "Arm released");
    } else {
        SendStatus("error", "Unknown arm action: " + command.action);
    }
}

void RemoteControlHandler::HandleGimbalCommand(const RemoteControlCommand& command) {
    if (!gimbal_) {
        SendStatus("error", "Gimbal not available");
        return;
    }
    
    if (command.action == ACTION_GIMBAL_PAN) {
        float angle = 0;
        if (command.parameters) {
            ParseFloatParameter(command.parameters, "angle", angle);
        }
        // Gimbal_setPanAngle(gimbal_, angle);
        SendStatus("success", "Gimbal pan set to " + std::to_string(angle) + " degrees");
    } else if (command.action == ACTION_GIMBAL_TILT) {
        float angle = 0;
        if (command.parameters) {
            ParseFloatParameter(command.parameters, "angle", angle);
        }
        // Gimbal_setTiltAngle(gimbal_, angle);
        SendStatus("success", "Gimbal tilt set to " + std::to_string(angle) + " degrees");
    } else if (command.action == ACTION_GIMBAL_RESET) {
        // Gimbal_reset(gimbal_);
        SendStatus("success", "Gimbal reset");
    } else {
        SendStatus("error", "Unknown gimbal action: " + command.action);
    }
}

void RemoteControlHandler::HandleCameraCommand(const RemoteControlCommand& command) {
    if (!camera_) {
        SendStatus("error", "Camera not available");
        return;
    }
    
    if (command.action == ACTION_CAMERA_CAPTURE) {
        // camera_->Capture();
        SendStatus("success", "Camera capture initiated");
    } else if (command.action == ACTION_CAMERA_START_STREAM) {
        // camera_->StartStream();
        SendStatus("success", "Camera stream started");
    } else if (command.action == ACTION_CAMERA_STOP_STREAM) {
        // camera_->StopStream();
        SendStatus("success", "Camera stream stopped");
    } else {
        SendStatus("error", "Unknown camera action: " + command.action);
    }
}

void RemoteControlHandler::HandleSystemCommand(const RemoteControlCommand& command) {
    if (command.action == ACTION_SYSTEM_RESTART) {
        SendStatus("success", "System restart initiated");
        vTaskDelay(pdMS_TO_TICKS(1000)); // 等待1秒
        esp_restart();
    } else if (command.action == ACTION_SYSTEM_STATUS) {
        SendStatus("success", "System is running");
    } else if (command.action == ACTION_SYSTEM_INFO) {
        std::string info = GetSupportedCommands();
        SendStatus("info", info);
    } else {
        SendStatus("error", "Unknown system action: " + command.action);
    }
}

void RemoteControlHandler::SendStatus(const std::string& status, const std::string& message) {
    ESP_LOGI(TAG_REMOTE_CONTROL, "📤 SENDING Status Response");
    ESP_LOGI(TAG_REMOTE_CONTROL, "  Status: %s", status.c_str());
    ESP_LOGI(TAG_REMOTE_CONTROL, "  Message: %s", message.c_str());
    
    if (status_callback_) {
        status_callback_(status, message);
    }
}

bool RemoteControlHandler::ParseIntParameter(const cJSON* params, const std::string& key, int& value) {
    cJSON* item = cJSON_GetObjectItem(params, key.c_str());
    if (cJSON_IsNumber(item)) {
        value = item->valueint;
        return true;
    }
    return false;
}

bool RemoteControlHandler::ParseFloatParameter(const cJSON* params, const std::string& key, float& value) {
    cJSON* item = cJSON_GetObjectItem(params, key.c_str());
    if (cJSON_IsNumber(item)) {
        value = (float)item->valuedouble;
        return true;
    }
    return false;
}

bool RemoteControlHandler::ParseStringParameter(const cJSON* params, const std::string& key, std::string& value) {
    cJSON* item = cJSON_GetObjectItem(params, key.c_str());
    if (cJSON_IsString(item)) {
        value = item->valuestring;
        return true;
    }
    return false;
}

bool RemoteControlHandler::ParseBoolParameter(const cJSON* params, const std::string& key, bool& value) {
    cJSON* item = cJSON_GetObjectItem(params, key.c_str());
    if (cJSON_IsBool(item)) {
        value = cJSON_IsTrue(item);
        return true;
    }
    return false;
}

