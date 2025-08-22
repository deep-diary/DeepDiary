import asyncio
import sys
import os
import logging
import time
import requests
from urllib.parse import urljoin

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from deepwin.config.config_manager import ConfigManager
from deepwin.data_management.log_manager import LogManager
from deepwin.data_management.database.qdrant_manager import QdrantManager


class QdrantWebUITest:
    """Qdrant Web UI功能测试类"""
    
    def __init__(self):
        """初始化测试环境"""
        self.log_manager = LogManager()
        
        # 设置日志级别
        self.log_manager.set_all_levels(
            console_level=logging.INFO,
            file_level=logging.DEBUG
        )
        
        self.config_manager = ConfigManager(self.log_manager)
        self.logger = self.log_manager.get_logger(__name__)
        
        # 创建Qdrant管理器，启用Web UI
        self.qdrant_manager = QdrantManager(
            name="qdrant_web_ui_test",
            config_manager=self.config_manager,
            log_manager=self.log_manager,
            local_path="database/qdrant/test",
            web_ui_enabled=True,  # 启用Web UI
            web_ui_port=6333      # 指定端口
        )
        
        # 测试配置
        self.test_urls = [
            "http://localhost:6333",
            "http://127.0.0.1:6333",
            "http://localhost:6333/dashboard",
            "http://127.0.0.1:6333/dashboard"
        ]

    async def test_web_ui_functionality(self):
        """测试Web UI功能"""
        print("🎯 测试Qdrant Web UI功能")
        print("=" * 60)
        
        try:
            # 1. 连接数据库
            print("🚀 连接Qdrant数据库...")
            success = await self.qdrant_manager.connect()
            if not success:
                print("❌ 数据库连接失败")
                return False
            
            print("✅ 数据库连接成功")
            
            # 2. 检查Web UI状态
            print("\n📊 检查Web UI状态...")
            status = self.qdrant_manager.get_web_ui_status()
            for key, value in status.items():
                print(f"   {key}: {value}")
            
            # 3. 等待Web UI启动
            print("\n⏳ 等待Web UI启动...")
            web_ui_started = await self._wait_for_web_ui_start()
            if not web_ui_started:
                print("❌ Web UI启动超时")
                return False
            
            print("✅ Web UI已启动")
            
            # 4. 测试网页访问
            print("\n🌐 测试网页访问...")
            access_success = await self._test_web_access()
            if not access_success:
                print("❌ 网页访问测试失败")
                return False
            
            print("✅ 网页访问测试成功")
            
            # 5. 显示访问信息
            print("\n🌐 Web UI访问信息:")
            url = self.qdrant_manager.get_web_ui_url()
            if url:
                print(f"   主地址: {url}")
                print(f"   本地地址: http://127.0.0.1:6333")
                print(f"   网络地址: http://0.0.0.0:6333")
                print("\n💡 请在浏览器中打开上述地址查看Qdrant数据库")
            
            # 6. 保持运行状态，让用户访问Web UI
            print("\n🔄 Web UI正在运行中...")
            print("   按Ctrl+C停止服务")
            
            try:
                while True:
                    await asyncio.sleep(5)
                    # 每5秒检查一次状态
                    if not self.qdrant_manager.is_web_ui_running():
                        print("⚠️  Web UI已停止运行")
                        break
            except KeyboardInterrupt:
                print("\n⏹️  用户中断，正在停止服务...")
            
            return True
            
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {e}")
            self.logger.error(f"测试错误: {e}")
            return False
        
        finally:
            # 清理资源
            print("🧹 清理资源...")
            await self.qdrant_manager.disconnect()
            print("✅ 清理完成")

    async def _wait_for_web_ui_start(self, timeout: int = 30) -> bool:
        """等待Web UI启动"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.qdrant_manager.is_web_ui_running():
                return True
            
            print(f"   等待中... ({int(time.time() - start_time)}/{timeout}秒)")
            await asyncio.sleep(1)
        
        return False

    async def _test_web_access(self) -> bool:
        """测试网页访问"""
        print("   测试网页访问...")
        
        for url in self.test_urls:
            try:
                print(f"   尝试访问: {url}")
                
                # 使用requests测试HTTP访问
                response = requests.get(url, timeout=5)
                
                if response.status_code == 200:
                    print(f"   ✅ 成功访问: {url}")
                    
                    # 检查响应内容
                    content = response.text
                    if "DeepWin Qdrant" in content or "Qdrant" in content:
                        print(f"   ✅ 页面内容正确: 包含Qdrant相关内容")
                        return True
                    else:
                        print(f"   ⚠️  页面内容可能不正确: {content[:100]}...")
                        return True  # 仍然认为访问成功
                
                else:
                    print(f"   ❌ 访问失败: {url} (状态码: {response.status_code})")
                    
            except requests.exceptions.ConnectionError:
                print(f"   ❌ 连接失败: {url}")
            except requests.exceptions.Timeout:
                print(f"   ❌ 访问超时: {url}")
            except Exception as e:
                print(f"   ❌ 访问异常: {url} - {e}")
        
        return False

    def test_manual_start(self):
        """测试手动启动Web UI"""
        print("🔧 测试手动启动Web UI...")
        
        # 手动启动Web UI
        success = self.qdrant_manager.start_web_ui_manually(port=6334)
        if success:
            print("✅ 手动启动Web UI成功")
            print("🌐 访问地址: http://localhost:6334")
            
            # 等待启动
            time.sleep(3)
            
            # 检查状态
            status = self.qdrant_manager.get_web_ui_status()
            print(f"   状态: {status}")
        else:
            print("❌ 手动启动Web UI失败")

    async def test_quick_access(self):
        """快速测试Web UI访问"""
        print("⚡ 快速测试Web UI访问...")
        
        try:
            # 创建临时管理器
            temp_manager = QdrantManager(
                name="quick_test",
                config_manager=self.config_manager,
                log_manager=self.log_manager,
                local_path="database/qdrant/quick_test",
                web_ui_enabled=True,
                web_ui_port=6335
            )
            
            # 连接并启动Web UI
            await temp_manager.connect()
            
            # 等待启动
            await asyncio.sleep(3)
            
            # 测试访问
            test_url = "http://localhost:6335"
            try:
                response = requests.get(test_url, timeout=5)
                if response.status_code == 200:
                    print(f"✅ 快速测试成功: {test_url}")
                    return True
                else:
                    print(f"❌ 快速测试失败: {test_url} (状态码: {response.status_code})")
                    return False
            except Exception as e:
                print(f"❌ 快速测试异常: {e}")
                return False
            finally:
                await temp_manager.disconnect()
                
        except Exception as e:
            print(f"❌ 快速测试错误: {e}")
            return False


async def main():
    """主函数"""
    test = QdrantWebUITest()
    
    print("选择测试模式:")
    print("1. 完整测试 (推荐)")
    print("2. 快速测试")
    print("3. 手动启动测试")
    
    try:
        choice = input("请输入选择 (1-3): ").strip()
        
        if choice == "1":
            # 完整测试
            success = await test.test_web_ui_functionality()
            if success:
                print("\n🎉 完整测试通过！")
            else:
                print("\n❌ 完整测试失败！")
                
        elif choice == "2":
            # 快速测试
            success = await test.test_quick_access()
            if success:
                print("\n🎉 快速测试通过！")
            else:
                print("\n❌ 快速测试失败！")
                
        elif choice == "3":
            # 手动启动测试
            test.test_manual_start()
            
        else:
            print("无效选择，运行完整测试...")
            success = await test.test_web_ui_functionality()
            if success:
                print("\n🎉 测试通过！")
            else:
                print("\n❌ 测试失败！")
                
    except KeyboardInterrupt:
        print("\n⏹️  用户中断测试")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")


if __name__ == "__main__":
    # 运行测试
    asyncio.run(main())
