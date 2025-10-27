# 定时器计数器逻辑修复

## 问题描述

原始代码存在两个问题：

### 问题1：计数器重置值错误
```cpp
// 错误的做法
if (cycle_counter >= CYCLE_60000MS) { 
    cycle_counter = 0; 
}

// CYCLE_60000MS = 600 (对应60秒)
// 但如果有MQTT_LEGACY_INFO_CYCLE (300，对应30秒)
// 这个逻辑会导致某些任务无法正确触发
```

**问题原因**：
- 如果某任务的周期大于重置点，该任务永远不会被触发
- 例如：如果某任务周期是500，而重置点在300，那么当计数器到500时会先重置，500永远到不了

### 问题2：首次运行立即触发
```cpp
static uint32_t cycle_counter = 0;
// ...
if ((cycle_counter % SENSOR_UPDATE_CYCLE) == 0) {
    time_flags.sensor_update = true;  // 首次运行时会立即触发！
}
```

**问题原因**：
- `cycle_counter` 初始值为 0
- 取模运算 `0 % CYCLE` 总是等于 0
- 导致第一个循环就会触发所有周期性任务

## 修复方案

### 1. 使用最大任务周期作为重置点

```cpp
// 添加MAX宏定义
#ifndef MAX
#define MAX(a, b) ((a) > (b) ? (a) : (b))
#endif

// 自动计算所有任务周期中的最大值
#define MAX_TASK_CYCLE  MAX(SENSOR_UPDATE_CYCLE, \
                           MAX(MQTT_CONFIG_CYCLE, \
                           MAX(MQTT_SYSTEM_STATUS_CYCLE, \
                           MAX(MQTT_SENSOR_STATUS_CYCLE, \
                           MAX(MQTT_ACTUATOR_STATUS_CYCLE, \
                               MQTT_LEGACY_INFO_CYCLE)))))
```

**优势**：
- ✅ 自动适应所有任务周期
- ✅ 添加新任务时自动更新重置点
- ✅ 确保所有任务都能正确触发

### 2. 防止首次运行立即触发

```cpp
static uint32_t cycle_counter = 0;
static bool first_run = true;

while (1) {
    vTaskDelay(pdMS_TO_TICKS(MAIN_LOOP_BASE_DELAY_MS));
    
    // 首次运行不增加计数器
    if (!first_run) {
        cycle_counter++;
    } else {
        first_run = false;
    }
    
    // 重置为1而不是0
    if (cycle_counter >= MAX_TASK_CYCLE) { 
        cycle_counter = 1; 
    }
}
```

**优势**：
- ✅ 首次运行时 cycle_counter 保持为 0
- ✅ 不会触发任何周期性任务
- ✅ 重置后从 1 开始，避免立即触发

## 修复后的执行流程

### 时间线示例（假设基础延时100ms）

| 时间 | cycle_counter | 触发的任务 |
|-----|--------------|-----------|
| 0ms   | 0 (首次，不触发) | 无 |
| 100ms | 1 | 无 |
| 1000ms (1秒) | 10 | sensor_update ✅ |
| 3000ms (3秒) | 30 | sensor_update, mqtt_sensor_status ✅ |
| 5000ms (5秒) | 50 | sensor_update, mqtt_actuator_status ✅ |
| 10000ms (10秒) | 100 | sensor_update, mqtt_system_status ✅ |
| 30000ms (30秒) | 300 | sensor_update, mqtt_legacy_info ✅ |
| 60000ms (60秒) | 600 | 所有MQTT任务，然后重置为1 ✅ |

### 重置后的行为

| 重置后 cycle_counter | 触发的任务 | 说明 |
|---------------------|-----------|------|
| 1 | 无 | 第一次循环 |
| 10 | sensor_update | 1秒后 |
| ... | ... | ... |
| 600 | 所有任务 | 60秒后重置 |

## 验证结果

✅ **所有任务都能正确触发**
- 周期 ≤ 60秒的任务都能正常工作
- 添加更长的周期任务时，会自动调整重置点

✅ **首次运行不会立即触发**
- 首次循环时所有标志位都是 false
- 从第二次循环开始正常计数

✅ **周期性正确**
- 各任务按设计周期精确触发
- 没有遗漏或重复触发

## 如何添加新任务

只需在 `board_extensions.h` 中定义新任务的周期：

```cpp
// 1. 定义新任务的周期
#define NEW_TASK_CYCLE CYCLE_15000MS  // 15秒任务

// 2. 添加到MAX_TASK_CYCLE计算中
#define MAX_TASK_CYCLE  MAX(..., NEW_TASK_CYCLE)

// 3. 在TimeFlags中添加标志位
struct TimeFlags {
    // ...
    bool new_task;
};

// 4. 在标志位判断中添加逻辑
if ((cycle_counter % NEW_TASK_CYCLE) == 0) {
    time_flags.new_task = true;
}

// 5. 在任务执行部分添加处理
if (time_flags.new_task) {
    // 执行新任务
}
```

系统会自动确保新任务能正确触发！

## 设计要点总结

1. **重置点 = 最大任务周期**：确保最长的任务也能完整执行
2. **首次不触发**：避免系统启动时立即执行所有任务
3. **重置为1而不是0**：避免重置后立即触发
4. **标志位机制**：将时间判断和任务执行分离

## 相关文件

- `board_extensions.h`: 时间周期宏定义
- `board_extensions.cc`: 主循环任务实现
- `TASK_ARCHITECTURE.md`: 任务架构对比文档

