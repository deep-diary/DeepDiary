#ifndef HTTP_STREAM_H
#define HTTP_STREAM_H

#include <string>
#include <memory>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <freertos/queue.h>
#include "esp32_camera.h"

/**
 * @brief HTTP MJPEG推流客户端
 * 
 * 通过HTTP POST方式推送MJPEG视频流到远程服务器
 * 使用multipart/x-mixed-replace格式
 */
class HttpStream {
public:
    /**
     * @brief 构造函数
     * @param camera 相机对象指针
     * @param server_url 服务器URL，例如 "http://34.172.161.212:8889/esp32cam"
     */
    HttpStream(Camera* camera, const std::string& server_url);
    
    ~HttpStream();

    /**
     * @brief 启动HTTP推流
     * @return true 成功，false 失败
     */
    bool Start();

    /**
     * @brief 停止HTTP推流
     */
    void Stop();

    /**
     * @brief 检查是否正在运行
     * @return true 正在运行，false 未运行
     */
    bool IsRunning() const { return running_; }

    /**
     * @brief 获取服务器URL
     * @return 服务器URL字符串
     */
    std::string GetServerUrl() const { return server_url_; }

    /**
     * @brief 设置帧率
     * @param fps 帧率（帧/秒）
     */
    void SetFrameRate(int fps);

    /**
     * @brief 设置JPEG质量
     * @param quality JPEG质量（0-100）
     */
    void SetJpegQuality(int quality) { jpeg_quality_ = quality; }

    /**
     * @brief 获取推送帧数统计
     * @return 已推送的帧数
     */
    uint32_t GetFrameCount() const { return frame_count_; }

private:
    Camera* camera_;                    // 相机对象
    std::string server_url_;            // 服务器URL
    std::string server_host_;           // 服务器主机名
    uint16_t server_port_;              // 服务器端口
    std::string server_path_;           // 服务器路径
    
    bool running_;                      // 运行状态
    int frame_rate_;                    // 帧率
    int jpeg_quality_;                  // JPEG质量
    uint32_t frame_count_;              // 帧计数器
    
    TaskHandle_t stream_task_;          // 推流任务句柄
    
    /**
     * @brief 解析URL
     * @param url 完整的URL字符串
     * @return true 成功，false 失败
     */
    bool ParseUrl(const std::string& url);
    
    /**
     * @brief 推流任务（静态方法）
     * @param pvParameters 任务参数（HttpStream对象指针）
     */
    static void StreamTask(void* pvParameters);
    
    /**
     * @brief 推送单个JPEG帧
     * @param jpeg_data JPEG数据指针
     * @param jpeg_size JPEG数据大小
     * @return true 成功，false 失败
     */
    bool PushFrame(const uint8_t* jpeg_data, size_t jpeg_size);
};

#endif // HTTP_STREAM_H

