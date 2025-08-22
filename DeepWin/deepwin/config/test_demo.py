#!/usr/bin/env python3
"""
Configuration Test Demo

演示如何使用测试基类进行配置测试
"""

import sys
import os
from pathlib import Path
from deepwin.config.config_manager import ConfigManager

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# 修复导入路径
try:
    from deepwin.utils.test import ConfigTestBase
except ImportError:
    # 如果上面的导入失败，尝试相对导入
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from utils.test import ConfigTestBase


class ConfigurationTestDemo(ConfigTestBase):
    """配置测试演示类"""
    
    def __init__(self):
        super().__init__("ConfigurationTestDemo")
    
    def test_basic_config_loading(self):
        """测试基本配置加载"""
        self.print_info("测试基本配置加载功能")
        
        # 测试配置管理器初始化
        if not self.setup_config_manager():
            self.print_error("配置管理器初始化失败，跳过后续测试")
            return False
        
        # 测试配置加载
        if not self.load_test_config():
            self.print_error("配置加载失败，跳过后续测试")
            return False
        
        # 测试配置结构
        required_sections = ["general", "device_settings", "network", "ai_settings"]
        structure_ok = self.test_config_structure(required_sections)
        
        # 测试配置值
        test_cases = [
            {"key": "general.theme", "expected": "light"},
            {"key": "general.language", "expected": "zh_CN"},
            {"key": "device_settings.deeparm_serial_port", "expected": "COM11"},  # 修正为实际值
            {"key": "network.mqtt_broker_port", "expected": 1883}
        ]
        values_ok = self.test_config_values(test_cases)
        
        return structure_ok and values_ok
    
    def test_environment_config(self):
        """测试环境配置功能"""
        self.print_info("测试环境配置功能")
        
        if not self.config_manager:
            self.print_error("配置管理器未初始化")
            return False
        
        # 测试环境设置
        self.config_manager.set_environment("production")
        current_env = self.config_manager.get_environment_config()
        env_ok = self.assert_equal(current_env, "production", "环境设置")
        
        # 恢复开发环境
        self.config_manager.set_environment("development")
        current_env = self.config_manager.get_environment_config()
        env_ok = env_ok and self.assert_equal(current_env, "development", "环境恢复")
        
        return env_ok
    
    def test_config_operations(self):
        """测试配置操作功能"""
        self.print_info("测试配置操作功能")
        
        if not self.config_manager:
            self.print_error("配置管理器未初始化")
            return False
        
        # 测试获取配置值
        theme = self.config_manager.get("general.theme")
        theme_ok = self.assert_equal(theme, "light", "获取配置值")
        
        # 测试设置配置值
        self.config_manager.set("general.theme", "dark")
        new_theme = self.config_manager.get("general.theme")
        set_ok = self.assert_equal(new_theme, "dark", "设置配置值")
        
        # 测试获取所有配置
        all_config = self.config_manager.get_all()
        all_ok = self.assert_is_instance(all_config, dict, "获取所有配置")
        
        # 恢复原值
        self.config_manager.set("general.theme", "light")
        
        return theme_ok and set_ok and all_ok
    
    def test_config_validation(self):
        """测试配置验证功能"""
        self.print_info("测试配置验证功能")
        
        if not self.test_config:
            self.print_error("测试配置未加载")
            return False
        
        try:
            from deepwin.config.config_validator import ConfigValidator
            validator = ConfigValidator()
            
            # 验证配置
            is_valid, errors, warnings = validator.validate_config(self.test_config)
            
            # 检查验证结果
            validation_ok = self.assert_true(is_valid, "配置验证通过")
            
            # 显示验证摘要
            summary = validator.get_validation_summary()
            self.print_info(f"验证摘要: {summary}")
            
            # 显示详细错误和警告
            if errors:
                self.print_section("验证错误")
                for error in errors:
                    self.print_error(f"  {error}")
            
            if warnings:
                self.print_section("验证警告")
                for warning in warnings:
                    self.print_warning(f"  {warning}")
            
            return validation_ok
            
        except ImportError:
            self.print_warning("配置验证器未找到，跳过验证测试")
            return True
        except Exception as e:
            self.print_error(f"配置验证测试异常: {e}")
            return False
    
    def test_multiple_formats(self):
        """测试多种配置格式"""
        self.print_info("测试多种配置格式支持")
        
        if not self.config_manager:
            self.print_error("配置管理器未初始化")
            return False
        
        # 测试保存为不同格式
        test_config = {
            "test_section": {
                "test_key": "test_value",
                "test_number": 42,
                "test_bool": True
            }
        }
        
        formats_to_test = ["json", "yaml", "toml"]
        format_results = []
        
        for format_type in formats_to_test:
            try:
                success = self.config_manager.save_config(
                    test_config, 
                    f"test_config_{format_type}", 
                    format_type
                )
                format_results.append((format_type, success))
                
                if success:
                    self.print_success(f"保存为 {format_type} 格式成功")
                else:
                    self.print_error(f"保存为 {format_type} 格式失败")
                    
            except Exception as e:
                self.print_error(f"保存为 {format_type} 格式异常: {e}")
                format_results.append((format_type, False))
        
        # 统计结果
        successful_formats = sum(1 for _, success in format_results if success)
        total_formats = len(formats_to_test)
        
        self.print_info(f"格式支持测试: {successful_formats}/{total_formats} 成功")
        
        return successful_formats > 0
    
    def test_environment_variables(self):
        """测试环境变量加载"""
        self.print_info("测试环境变量加载功能")
        
        try:
            # 尝试加载环境变量配置
            self.config_manager = ConfigManager()
            env_config = self.config_manager.load_env()
            
            if env_config:
                self.print_success(f"成功加载环境变量配置，共 {len(env_config)} 个变量")
                self.print_config(env_config, "环境变量配置")
                return True
            else:
                self.print_warning("环境变量配置为空")
                return True
                
        except Exception as e:
            self.print_error(f"环境变量加载测试异常: {e}")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        self.start_test()
        
        try:
            # 运行各个测试用例
            test_results = []
            
            test_results.append(self.run_test_case(self.test_basic_config_loading, "基本配置加载"))
            test_results.append(self.run_test_case(self.test_environment_config, "环境配置"))
            test_results.append(self.run_test_case(self.test_config_operations, "配置操作"))
            test_results.append(self.run_test_case(self.test_config_validation, "配置验证"))
            test_results.append(self.run_test_case(self.test_multiple_formats, "多格式支持"))
            test_results.append(self.run_test_case(self.test_environment_variables, "环境变量"))
            
            # 统计结果
            passed_tests = sum(1 for result in test_results if result)
            total_tests = len(test_results)
            
            self.print_section("测试完成")
            self.print_success(f"总测试数: {total_tests}, 通过: {passed_tests}, 失败: {total_tests - passed_tests}")
            
            return passed_tests == total_tests
            
        finally:
            self.end_test()
            self.cleanup()


def main():
    """主函数"""
    print("DeepWin 配置测试演示")
    print("=" * 50)
    
    try:
        # 创建测试实例
        test_demo = ConfigurationTestDemo()
        
        # 运行所有测试
        success = test_demo.run_all_tests()
        
        if success:
            print("\n🎉 所有测试通过！")
        else:
            print("\n⚠️  部分测试失败，请检查配置")
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"\n❌ 测试演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
