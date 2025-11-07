# Google Fonts 访问问题解决方案

## 问题说明

在中国大陆，浏览器无法直接访问 `fonts.googleapis.com` 和 `fonts.gstatic.com`，导致：
- Google Fonts CSS 加载超时
- 字体文件无法下载
- 页面加载变慢

## 解决方案

### 方案 1：Nginx 代理（已配置但需要前端配合）

已配置代理端点：
- `https://www.deep-diary.com/_proxy/fonts.googleapis.com/` → 代理到 Google Fonts API
- `https://www.deep-diary.com/_proxy/fonts.gstatic.com/` → 代理到 Google Fonts 字体文件

**注意**：Gradio 在前端直接请求 `fonts.googleapis.com`，无法通过 Nginx 拦截。需要：
1. 修改 Gradio 源码（不推荐）
2. 使用浏览器扩展拦截（不实用）
3. 使用本地字体替代（推荐）

### 方案 2：使用本地字体（推荐）

由于 Gradio 是第三方库，无法直接修改其字体加载逻辑，最佳方案是：

1. **忽略 Google Fonts 错误**：Gradio 会自动使用备用字体
2. **使用系统字体**：浏览器会使用系统默认字体
3. **不影响功能**：只是字体样式略有不同

### 方案 3：使用国内字体 CDN

如果需要特定字体，可以考虑：
- 360 前端静态资源库：`https://cdn.baomitu.com/`
- 字节跳动静态资源：`https://lf3-cdn-tos.bytecdntp.com/`
- 七牛云 CDN

但这些需要修改 Gradio 源码，不推荐。

## 当前配置说明

1. **manifest.json**：已创建，解决 404 错误
2. **Google Fonts 代理**：已配置代理端点（需要前端配合使用）
3. **静态资源缓存**：已优化，提升加载速度

## 建议

**最佳实践**：忽略 Google Fonts 错误，使用系统默认字体。这不会影响功能，只是视觉效果略有不同。

如果必须使用特定字体，建议：
1. 下载字体文件到本地
2. 通过自定义 CSS 覆盖 Gradio 的字体设置
3. 在 Nginx 中配置字体文件服务

