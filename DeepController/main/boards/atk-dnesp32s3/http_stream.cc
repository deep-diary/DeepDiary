#include "http_stream.h"
#include <esp_log.h>
#include <esp_camera.h>
#include <img_converters.h>
#include <lwip/sockets.h>
#include <lwip/netdb.h>
#include <string.h>
#include <wifi_station.h>

#define TAG "HttpStream"

HttpStream::HttpStream(Camera* camera, const std::string& server_url)
    : camera_(camera), server_url_(server_url), server_port_(80),
      running_(false), frame_rate_(10), jpeg_quality_(80), 
      frame_count_(0), stream_task_(nullptr) {
    
    ParseUrl(server_url);
}

HttpStream::~HttpStream() {
    Stop();
}

bool HttpStream::ParseUrl(const std::string& url) {
    // 解析 http://host:port/path
    size_t proto_pos = url.find("://");
    if (proto_pos == std::string::npos) {
        ESP_LOGE(TAG, "URL格式错误：缺少协议");
        return false;
    }
    
    size_t host_start = proto_pos + 3;
    size_t port_pos = url.find(":", host_start);
    size_t path_pos = url.find("/", host_start);
    
    if (path_pos == std::string::npos) {
        ESP_LOGE(TAG, "URL格式错误：缺少路径");
        return false;
    }
    
    // 提取主机名
    if (port_pos != std::string::npos && port_pos < path_pos) {
        server_host_ = url.substr(host_start, port_pos - host_start);
        server_port_ = std::stoi(url.substr(port_pos + 1, path_pos - port_pos - 1));
    } else {
        server_host_ = url.substr(host_start, path_pos - host_start);
        server_port_ = 80;
    }
    
    // 提取路径
    server_path_ = url.substr(path_pos);
    
    ESP_LOGI(TAG, "解析URL - 服务器: %s, 端口: %d, 路径: %s", 
             server_host_.c_str(), server_port_, server_path_.c_str());
    
    return true;
}

void HttpStream::SetFrameRate(int fps) {
    frame_rate_ = fps;
    ESP_LOGI(TAG, "设置帧率: %d fps", frame_rate_);
}

bool HttpStream::Start() {
    if (running_) {
        ESP_LOGW(TAG, "HTTP推流已在运行");
        return true;
    }
    
    if (camera_ == nullptr) {
        ESP_LOGE(TAG, "相机未初始化");
        return false;
    }
    
    // 创建推流任务
    BaseType_t ret = xTaskCreate(StreamTask, "http_stream", 8192, this, 5, &stream_task_);
    if (ret != pdPASS) {
        ESP_LOGE(TAG, "创建推流任务失败");
        return false;
    }
    
    running_ = true;
    ESP_LOGI(TAG, "HTTP MJPEG推流启动成功");
    ESP_LOGI(TAG, "服务器地址: %s", server_url_.c_str());
    ESP_LOGI(TAG, "帧率: %d fps, JPEG质量: %d", frame_rate_, jpeg_quality_);
    
    return true;
}

void HttpStream::Stop() {
    if (!running_) {
        return;
    }
    
    running_ = false;
    
    if (stream_task_ != nullptr) {
        vTaskDelete(stream_task_);
        stream_task_ = nullptr;
    }
    
    ESP_LOGI(TAG, "HTTP推流已停止");
}

void HttpStream::StreamTask(void* pvParameters) {
    HttpStream* stream = static_cast<HttpStream*>(pvParameters);
    
    int sock = -1;
    bool connected = false;
    
    ESP_LOGI(TAG, "HTTP推流任务启动");
    
    while (stream->running_) {
        // 建立HTTP连接
        if (!connected) {
            struct sockaddr_in server_addr;
            struct hostent* he = gethostbyname(stream->server_host_.c_str());
            
            if (he == nullptr) {
                ESP_LOGE(TAG, "DNS解析失败: %s", stream->server_host_.c_str());
                vTaskDelay(pdMS_TO_TICKS(5000));
                continue;
            }
            
            sock = socket(AF_INET, SOCK_STREAM, 0);
            if (sock < 0) {
                ESP_LOGE(TAG, "创建socket失败");
                vTaskDelay(pdMS_TO_TICKS(5000));
                continue;
            }
            
            memset(&server_addr, 0, sizeof(server_addr));
            server_addr.sin_family = AF_INET;
            server_addr.sin_port = htons(stream->server_port_);
            memcpy(&server_addr.sin_addr.s_addr, he->h_addr, he->h_length);
            
            ESP_LOGI(TAG, "正在连接到 %s:%d...", stream->server_host_.c_str(), stream->server_port_);
            
            if (connect(sock, (struct sockaddr*)&server_addr, sizeof(server_addr)) < 0) {
                ESP_LOGE(TAG, "连接失败");
                close(sock);
                sock = -1;
                vTaskDelay(pdMS_TO_TICKS(5000));
                continue;
            }
            
            ESP_LOGI(TAG, "HTTP连接建立成功");
            
            // 发送HTTP请求头
            char header[512];
            snprintf(header, sizeof(header),
                "POST %s HTTP/1.1\r\n"
                "Host: %s:%d\r\n"
                "Content-Type: multipart/x-mixed-replace; boundary=frame\r\n"
                "Connection: keep-alive\r\n"
                "\r\n",
                stream->server_path_.c_str(),
                stream->server_host_.c_str(),
                stream->server_port_);
            
            if (send(sock, header, strlen(header), 0) < 0) {
                ESP_LOGE(TAG, "发送HTTP头失败");
                close(sock);
                sock = -1;
                vTaskDelay(pdMS_TO_TICKS(5000));
                continue;
            }
            
            ESP_LOGI(TAG, "HTTP请求头发送成功，开始推流...");
            connected = true;
        }
        
        // 获取相机帧（直接使用ESP-IDF API）
        camera_fb_t* fb = esp_camera_fb_get();
        if (fb == nullptr) {
            ESP_LOGD(TAG, "获取相机帧失败");
            vTaskDelay(pdMS_TO_TICKS(100));
            continue;
        }
        
        // 转换为JPEG（如果需要）
        uint8_t* jpeg_data = nullptr;
        size_t jpeg_size = 0;
        bool need_free = false;
        
        if (fb->format == PIXFORMAT_JPEG) {
            jpeg_data = fb->buf;
            jpeg_size = fb->len;
        } else {
            // 使用frame2jpg_cb转换
            std::pair<uint8_t*, size_t> jpeg_result = {nullptr, 0};
            need_free = frame2jpg_cb(fb, stream->jpeg_quality_,
                [](void* arg, size_t index, const void* data, size_t len) -> unsigned int {
                    auto* result = (std::pair<uint8_t*, size_t>*)arg;
                    if (index == 0) {
                        result->first = (uint8_t*)malloc(len + 100000);
                        result->second = 0;
                    }
                    if (result->first != nullptr) {
                        memcpy(result->first + result->second, data, len);
                        result->second += len;
                    }
                    return len;
                }, &jpeg_result);
            
            jpeg_data = jpeg_result.first;
            jpeg_size = jpeg_result.second;
        }
        
        // 发送JPEG帧
        if (jpeg_data != nullptr && jpeg_size > 0) {
            // 构造multipart boundary
            char boundary[256];
            snprintf(boundary, sizeof(boundary),
                "\r\n--frame\r\n"
                "Content-Type: image/jpeg\r\n"
                "Content-Length: %zu\r\n"
                "\r\n",
                jpeg_size);
            
            // 发送boundary
            if (send(sock, boundary, strlen(boundary), 0) < 0) {
                ESP_LOGE(TAG, "发送boundary失败，连接断开");
                close(sock);
                sock = -1;
                connected = false;
            } else {
                // 发送JPEG数据
                ssize_t sent = send(sock, jpeg_data, jpeg_size, 0);
                if (sent < 0 || (size_t)sent != jpeg_size) {
                    ESP_LOGE(TAG, "发送JPEG数据失败，连接断开");
                    close(sock);
                    sock = -1;
                    connected = false;
                } else {
                    stream->frame_count_++;
                    if (stream->frame_count_ % 100 == 0) {
                        ESP_LOGI(TAG, "已推送 %lu 帧", (unsigned long)stream->frame_count_);
                    }
                }
            }
        }
        
        // 释放资源
        if (need_free && jpeg_data != nullptr) {
            free(jpeg_data);
        }
        esp_camera_fb_return(fb);
        
        // 按帧率延迟
        int delay_ms = 1000 / stream->frame_rate_;
        vTaskDelay(pdMS_TO_TICKS(delay_ms));
    }
    
    // 清理
    if (sock >= 0) {
        close(sock);
    }
    
    ESP_LOGI(TAG, "HTTP推流任务结束，共推送 %lu 帧", (unsigned long)stream->frame_count_);
    vTaskDelete(NULL);
}

bool HttpStream::PushFrame(const uint8_t* jpeg_data, size_t jpeg_size) {
    // 这个方法可以用于外部推送单帧，暂时未实现
    return false;
}

