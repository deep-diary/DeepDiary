# 按键驱动模块

## 概述

本模块提供 ATK-DNESP32S3 开发板的按键驱动功能，支持轮询方式检测按键状态。

## 功能特性

- ✅ 轮询方式检测按键状态
- ✅ 按键去抖动处理
- ✅ 支持连续按键检测模式
- ✅ 多按键支持（KEY0、BOOT）
- ✅ 低功耗唤醒支持

## 按键定义

### KEY0 按键（用户按键）

- **GPIO 引脚**: `GPIO_NUM_2`
- **功能**: 唤醒/休眠控制
- **键值**: `KEY0_PRES` (2)

### BOOT 按键（系统按键）

- **GPIO 引脚**: `GPIO_NUM_0`
- **功能**: 系统启动按键（保留用于系统功能）
- **键值**: `BOOT_PRES` (1)

## 使用方法

### 1. 初始化按键

```c
#include "btn/key.h"

void app_init(void) {
    key_init();  // 初始化按键
}
```

### 2. 扫描按键

在主循环中调用 `key_scan()` 函数：

```c
void main_loop(void) {
    uint8_t key_val = key_scan(0);  // 不支持连续按
    
    if (key_val == KEY0_PRES) {
        // 处理 KEY0 按键事件
        ESP_LOGI("APP", "KEY0 按键按下");
    } else if (key_val == BOOT_PRES) {
        // 处理 BOOT 按键事件
        ESP_LOGI("APP", "BOOT 按键按下");
    }
}
```

### 3. 按键扫描模式

```c
// 模式 0: 不支持连续按
// 按键按下不放时，只有第一次调用会返回键值
uint8_t key_val = key_scan(0);

// 模式 1: 支持连续按
// 按键按下不放时，每次调用都会返回键值
uint8_t key_val = key_scan(1);
```

## 文件说明

- `key.h`: 按键头文件，定义按键引脚、键值和函数声明
- `key.c`: 按键驱动实现，包含初始化和扫描函数
- `KEY_USAGE.md`: 详细的功能说明文档和使用指南

## 应用示例

### 唤醒/休眠控制

在 `board_extensions.cc` 中实现了基于 KEY0 按键的唤醒/休眠功能：

```c
uint8_t key_val = key_scan(0);
if (key_val == KEY0_PRES) {
    if (is_sleep_mode) {
        // 从休眠中唤醒
        wake_up_device();
    } else {
        // 进入休眠模式
        enter_sleep_mode();
    }
}
```

详细说明请参考 `KEY_USAGE.md`。

## 扩展按键

如果需要添加更多按键，请参考 `KEY_USAGE.md` 中的"扩展功能"章节。

## 相关文档

- [KEY_USAGE.md](./KEY_USAGE.md) - 详细的功能说明和使用指南
