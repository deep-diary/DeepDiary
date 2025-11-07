# 网页加载性能优化说明

## 问题分析

根据浏览器控制台日志，发现以下性能问题：

### 1. Google Fonts 连接超时
```
GET https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@400;600&display=swap 
net::ERR_CONNECTION_TIMED_OUT
```
**原因**：服务器可能无法访问 Google Fonts（网络限制或防火墙）

### 2. 字体文件加载慢
```
Fallback font will be used while loading: 
https://www.deep-diary.com/static/fonts/IBMPlexMono/IBMPlexMono-Regular.woff2
```
**原因**：Gradio 的静态字体文件加载较慢

### 3. manifest.json 404 错误
```
GET https://www.deep-diary.com/manifest.json 404 (Not Found)
```
**原因**：PWA manifest 文件缺失（不影响功能，但会产生错误日志）

## 已实施的优化方案

### 1. Nginx 配置优化

#### Gzip 压缩
- 启用 gzip 压缩，减少传输数据量
- 支持字体、CSS、JS 等静态资源压缩

#### 静态资源缓存
- 为静态资源（字体、图片、CSS、JS）设置 1 天缓存
- 减少重复请求，提升加载速度

#### WebSocket 支持
- 添加 WebSocket 支持，提升实时通信性能

### 2. Gradio 配置优化

#### 性能参数
- `enable_queue=True`: 启用队列机制，提高并发处理能力
- `max_threads=10`: 限制线程数，避免资源过度消耗
- `show_error=False`: 减少错误信息显示，提升性能

## 预期效果

1. **静态资源加载速度提升**：通过缓存和压缩，字体、CSS、JS 文件加载更快
2. **减少网络请求**：缓存机制减少重复请求
3. **提升并发性能**：队列机制提高多用户访问时的响应速度

## 注意事项

1. **Google Fonts 超时**：这是网络问题，不影响功能，Gradio 会使用备用字体
2. **manifest.json 404**：这是 PWA 相关文件，不影响核心功能
3. **首次加载**：首次访问时仍需要加载所有资源，后续访问会更快（缓存生效）

## 进一步优化建议

如果仍有性能问题，可以考虑：

1. **使用 CDN**：将静态资源部署到 CDN
2. **本地字体**：将 Google Fonts 替换为本地字体文件
3. **资源预加载**：在 HTML 中添加 preload 标签
4. **服务端渲染优化**：优化 Gradio 的渲染性能

