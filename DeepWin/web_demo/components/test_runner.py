"""
测试运行器组件
用于运行各种配置测试
"""

import streamlit as st
import sys
import os
from pathlib import Path

# 添加项目根目录到路径（修正路径）
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

class TestRunner:
    """测试运行器"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
    
    def run_basic_config_test(self):
        """运行基本配置测试"""
        try:
            st.write("🧪 运行基本配置测试...")
            
            # 测试配置加载
            config_data = self.config_manager.get_all()
            if config_data:
                st.success("✅ 配置加载成功")
                
                # 测试基本配置项
                test_cases = [
                    ("general.theme", "light"),
                    ("device_settings.deeparm_serial_port", "COM11"),
                    ("api.llm_api_key", None)  # 可能为空
                ]
                
                passed = 0
                total = len(test_cases)
                
                for key_path, expected_value in test_cases:
                    try:
                        actual_value = self.config_manager.get(key_path)
                        if expected_value is None or actual_value == expected_value:
                            st.success(f"✅ {key_path}: {actual_value}")
                            passed += 1
                        else:
                            st.warning(f"⚠️ {key_path}: 期望 {expected_value}, 实际 {actual_value}")
                    except Exception as e:
                        st.error(f"❌ {key_path}: 获取失败 - {str(e)}")
                
                # 显示测试结果
                st.write(f"**测试结果**: {passed}/{total} 通过")
                if passed == total:
                    st.success("🎉 所有基本配置测试通过！")
                else:
                    st.warning("⚠️ 部分测试未通过，请检查配置")
                    
            else:
                st.error("❌ 配置加载失败")
                
        except Exception as e:
            st.error(f"❌ 基本配置测试失败: {str(e)}")
    
    def run_config_validation_test(self):
        """运行配置验证测试"""
        try:
            st.write("🧪 运行配置验证测试...")
            
            config_data = self.config_manager.get_all()
            if not config_data:
                st.error("❌ 没有配置数据可验证")
                return
            
            # 验证配置结构
            required_sections = ["general", "device_settings", "api"]
            missing_sections = []
            
            for section in required_sections:
                if section in config_data:
                    st.success(f"✅ 配置节 '{section}' 存在")
                else:
                    st.warning(f"⚠️ 配置节 '{section}' 缺失")
                    missing_sections.append(section)
            
            # 验证配置值
            validation_results = []
            
            # 检查串口配置
            try:
                serial_port = self.config_manager.get("device_settings.deeparm_serial_port")
                if serial_port and serial_port.startswith("COM"):
                    validation_results.append(("串口配置", "✅ 有效", "green"))
                else:
                    validation_results.append(("串口配置", "⚠️ 无效", "orange"))
            except:
                validation_results.append(("串口配置", "❌ 缺失", "red"))
            
            # 检查API配置
            try:
                api_key = self.config_manager.get("api.llm_api_key")
                if api_key:
                    validation_results.append(("API密钥", "✅ 已配置", "green"))
                else:
                    validation_results.append(("API密钥", "⚠️ 未配置", "orange"))
            except:
                validation_results.append(("API密钥", "❌ 缺失", "red"))
            
            # 显示验证结果
            st.write("**配置验证结果**")
            for item, status, color in validation_results:
                if color == "green":
                    st.success(f"{item}: {status}")
                elif color == "orange":
                    st.warning(f"{item}: {status}")
                else:
                    st.error(f"{item}: {status}")
            
            # 总结
            if not missing_sections and all(r[2] == "green" for r in validation_results):
                st.success("🎉 配置验证完全通过！")
            elif not missing_sections:
                st.warning("⚠️ 配置结构完整，但部分值需要配置")
            else:
                st.error("❌ 配置结构不完整，请检查配置")
                
        except Exception as e:
            st.error(f"❌ 配置验证测试失败: {str(e)}")
    
    def run_env_loading_test(self):
        """运行环境变量加载测试"""
        try:
            st.write("🧪 运行环境变量加载测试...")
            
            # 检查环境变量加载
            env_vars = {}
            for key, value in os.environ.items():
                if key.startswith(('DEEPWIN_', 'LLM_', 'DEEPARM_')):
                    env_vars[key] = value
            
            if env_vars:
                st.success(f"✅ 找到 {len(env_vars)} 个相关环境变量")
                
                # 显示环境变量
                for key, value in env_vars.items():
                    # 隐藏敏感信息
                    if "key" in key.lower() or "password" in key.lower():
                        display_value = "*" * 8
                    else:
                        display_value = value
                    
                    st.info(f"{key}: {display_value}")
                
                # 测试环境变量优先级
                st.write("**环境变量优先级测试**")
                
                # 模拟环境变量覆盖配置
                test_key = "DEEPWIN_TEST_VALUE"
                test_value = "environment_override"
                
                # 设置环境变量
                os.environ[test_key] = test_value
                
                try:
                    # 重新加载配置
                    self.config_manager._load_env()
                    st.success("✅ 环境变量重新加载成功")
                except Exception as e:
                    st.error(f"❌ 环境变量重新加载失败: {str(e)}")
                
                # 清理测试环境变量
                if test_key in os.environ:
                    del os.environ[test_key]
                    
            else:
                st.info("ℹ️ 未找到相关的环境变量")
                st.write("**提示**: 可以创建 `.env` 文件来配置环境变量")
                
        except Exception as e:
            st.error(f"❌ 环境变量加载测试失败: {str(e)}")
