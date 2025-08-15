# services/cloud_communication/mcp_client_wrappers/data_adapters.py
from typing import Dict, Any, List

class NewsDataAdapter:
    """将 NewsFeedMCP 响应转换为 DeepDiary 统一的新闻数据模型。"""
    @staticmethod
    def adapt(raw_news_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        adapted_articles = []
        for article in raw_news_data.get("articles", []):
            adapted_articles.append({
                "title": article.get("title", "无标题"),
                "summary": article.get("description", "无描述"),
                "source": article.get("source", {}).get("name", "未知来源"),
                "url": article.get("url"),
                "publish_date": article.get("publishedAt"),
                # ... 更多字段映射
            })
        return adapted_articles

class WeatherDataAdapter:
    """
    将 Amap Maps MCP 的 maps_weather 工具响应转换为 DeepDiary 统一的天气数据模型。
    响应结构可能因 MCP 服务而异，这里假设一个简化的结构。
    """
    @staticmethod
    def adapt(raw_weather_data: Dict[str, Any]) -> Dict[str, Any]:
        # 假设 raw_weather_data 是 maps_weather 工具返回的直接数据
        # 实际 MCP 响应结构可能需要根据 mcp.so 提供的工具文档来精确适配
        # 示例响应结构可能类似：{"status": "1", "lives": [...]}
        if raw_weather_data.get("status") == "1" and raw_weather_data.get("lives"):
            live_weather = raw_weather_data["lives"][0]
            adapted_weather = {
                "province": live_weather.get("province"),
                "city": live_weather.get("city"),
                "weather": live_weather.get("weather"),
                "temperature": live_weather.get("temperature"),
                "winddirection": live_weather.get("winddirection"),
                "windpower": live_weather.get("windpower"),
                "humidity": live_weather.get("humidity"),
                "reporttime": live_weather.get("reporttime")
            }
            return adapted_weather
        return {"error": "无法解析天气数据"}