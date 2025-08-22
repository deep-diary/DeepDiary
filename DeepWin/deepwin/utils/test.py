#!/usr/bin/env python3
"""
Test Base Class for DeepWin

提供测试相关的公共方法和工具函数
"""

import os
import sys
import time
import logging
from typing import Any, Dict, List, Optional, Callable
from pathlib import Path
from datetime import datetime
from deepwin.config.config_manager import ConfigManager

class TestBase:
    """测试基类，提供常用的测试辅助方法"""
    
    def __init__(self, test_name: str = None):
        self.test_name = test_name or self.__class__.__name__
        self.logger = self._setup_logger()
        self.test_start_time = None
        self.test_results = []
        
    def _setup_logger(self) -> logging.Logger:
        """设置测试日志器"""
        logger = logging.getLogger(f"test.{self.test_name}")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def print_header(self, title: str, char: str = "=", width: int = 60):
        """打印测试标题"""
        print(f"\n{char * width}")
        print(f"{title.center(width)}")
        print(f"{char * width}")
    
    def print_section(self, title: str, char: str = "-", width: int = 50):
        """打印测试小节标题"""
        print(f"\n{char * width}")
        print(f"{title.center(width)}")
        print(f"{char * width}")
    
    def print_result(self, test_name: str, success: bool, message: str = ""):
        """打印测试结果"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
        if message:
            print(f"    {message}")
        
        # 记录结果
        self.test_results.append({
            'test_name': test_name,
            'success': success,
            'message': message,
            'timestamp': datetime.now()
        })
    
    def print_info(self, message: str, indent: int = 0):
        """打印信息"""
        indent_str = " " * indent
        print(f"{indent_str}ℹ️  {message}")
    
    def print_warning(self, message: str, indent: int = 0):
        """打印警告"""
        indent_str = " " * indent
        print(f"{indent_str}⚠️  {message}")
    
    def print_error(self, message: str, indent: int = 0):
        """打印错误"""
        indent_str = " " * indent
        print(f"{indent_str}❌ {message}")
    
    def print_success(self, message: str, indent: int = 0):
        """打印成功信息"""
        indent_str = " " * indent
        print(f"{indent_str}✅ {message}")
    
    def print_config(self, config: Dict[str, Any], title: str = "配置信息"):
        """打印配置信息"""
        self.print_section(title)
        for key, value in config.items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for sub_key, sub_value in value.items():
                    print(f"    {sub_key}: {sub_value}")
            else:
                print(f"  {key}: {value}")
    
    def print_table(self, headers: List[str], rows: List[List[Any]], title: str = "数据表格"):
        """打印表格数据"""
        self.print_section(title)
        
        # 计算每列的最大宽度
        col_widths = []
        for i, header in enumerate(headers):
            max_width = len(str(header))
            for row in rows:
                if i < len(row):
                    max_width = max(max_width, len(str(row[i])))
            col_widths.append(max_width)
        
        # 打印表头
        header_str = " | ".join(f"{h:<{w}}" for h, w in zip(headers, col_widths))
        print(f"  {header_str}")
        print(f"  {'-' * len(header_str)}")
        
        # 打印数据行
        for row in rows:
            row_str = " | ".join(f"{str(cell):<{w}}" for cell, w in zip(row, col_widths))
            print(f"  {row_str}")
    
    def start_test(self, test_name: str = None):
        """开始测试"""
        test_name = test_name or self.test_name
        self.test_start_time = time.time()
        self.logger.info(f"开始测试: {test_name}")
        self.print_header(f"开始测试: {test_name}")
    
    def end_test(self, test_name: str = None):
        """结束测试"""
        test_name = test_name or self.test_name
        if self.test_start_time:
            duration = time.time() - self.test_start_time
            self.logger.info(f"测试完成: {test_name}, 耗时: {duration:.2f}秒")
            self.print_header(f"测试完成: {test_name}", char="=")
            print(f"总耗时: {duration:.2f}秒")
            
            # 打印测试结果摘要
            self.print_test_summary()
    
    def print_test_summary(self):
        """打印测试结果摘要"""
        if not self.test_results:
            return
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        self.print_section("测试结果摘要")
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests} ✅")
        print(f"失败: {failed_tests} ❌")
        print(f"成功率: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            self.print_section("失败测试详情")
            for result in self.test_results:
                if not result['success']:
                    print(f"  ❌ {result['test_name']}: {result['message']}")
    
    def assert_true(self, condition: bool, message: str = "") -> bool:
        """断言条件为真"""
        success = bool(condition)
        self.print_result("断言检查", success, message)
        return success
    
    def assert_false(self, condition: bool, message: str = "") -> bool:
        """断言条件为假"""
        success = not bool(condition)
        self.print_result("断言检查", success, message)
        return success
    
    def assert_equal(self, actual: Any, expected: Any, message: str = "") -> bool:
        """断言两个值相等"""
        success = actual == expected
        msg = f"{message} - 期望: {expected}, 实际: {actual}" if message else f"期望: {expected}, 实际: {actual}"
        self.print_result("相等性检查", success, msg)
        return success
    
    def assert_not_equal(self, actual: Any, expected: Any, message: str = "") -> bool:
        """断言两个值不相等"""
        success = actual != expected
        msg = f"{message} - 不应等于: {expected}, 实际: {actual}" if message else f"不应等于: {expected}, 实际: {actual}"
        self.print_result("不等性检查", success, msg)
        return success
    
    def assert_in(self, item: Any, container: Any, message: str = "") -> bool:
        """断言项目在容器中"""
        success = item in container
        msg = f"{message} - {item} 应在 {container} 中" if message else f"{item} 应在 {container} 中"
        self.print_result("包含性检查", success, msg)
        return success
    
    def assert_not_in(self, item: Any, container: Any, message: str = "") -> bool:
        """断言项目不在容器中"""
        success = item not in container
        msg = f"{message} - {item} 不应在 {container} 中" if message else f"{item} 不应在 {container} 中"
        self.print_result("不包含性检查", success, msg)
        return success
    
    def assert_is_instance(self, obj: Any, cls: type, message: str = "") -> bool:
        """断言对象是指定类型的实例"""
        success = isinstance(obj, cls)
        msg = f"{message} - 期望类型: {cls.__name__}, 实际类型: {type(obj).__name__}" if message else f"期望类型: {cls.__name__}, 实际类型: {type(obj).__name__}"
        self.print_result("类型检查", success, msg)
        return success
    
    def run_test_case(self, test_func: Callable, test_name: str = None):
        """运行测试用例"""
        test_name = test_name or test_func.__name__
        self.print_section(f"运行测试: {test_name}")
        
        try:
            start_time = time.time()
            result = test_func()
            duration = time.time() - start_time
            
            if result is None or result:
                self.print_success(f"测试 {test_name} 通过", indent=2)
            else:
                self.print_error(f"测试 {test_name} 失败", indent=2)
            
            print(f"    耗时: {duration:.2f}秒")
            return result
            
        except Exception as e:
            self.print_error(f"测试 {test_name} 异常: {e}", indent=2)
            self.logger.error(f"测试异常: {e}", exc_info=True)
            return False
    
    def cleanup(self):
        """清理测试资源"""
        self.logger.info("清理测试资源")
        # 子类可以重写此方法进行特定的清理工作


class ConfigTestBase(TestBase):
    """配置测试基类"""
    
    def __init__(self, test_name: str = None):
        super().__init__(test_name)
        self.config_manager: ConfigManager = None
        self.test_config = None
    
    def setup_config_manager(self, config_dir: str = None):
        """设置配置管理器"""
        try:
            # 创建配置管理器实例，传入None作为log_manager
            self.config_manager = ConfigManager(log_manager=None, config_dir=config_dir)
            self.print_success("配置管理器初始化成功")
            return True
        except ImportError as e:
            self.print_error(f"导入配置管理器失败: {e}")
            return False
        except Exception as e:
            self.print_error(f"配置管理器初始化失败: {e}")
            return False
    
    def load_test_config(self, config_name: str = "config"):
        """加载测试配置"""
        if not self.config_manager:
            self.print_error("配置管理器未初始化")
            return False
        
        try:
            # 配置管理器在初始化时已经加载了配置，直接获取
            self.test_config = self.config_manager.get_all()
            self.print_success(f"成功加载测试配置: {config_name}")
            self.print_config(self.test_config, "测试配置")
            return True
        except Exception as e:
            self.print_error(f"加载测试配置失败: {e}")
            return False
    
    def test_config_structure(self, required_sections: List[str]):
        """测试配置结构"""
        if not self.test_config:
            self.print_error("测试配置未加载")
            return False
        
        self.print_section("测试配置结构")
        all_passed = True
        
        for section in required_sections:
            if section in self.test_config:
                self.print_success(f"配置段 {section} 存在")
            else:
                self.print_error(f"配置段 {section} 缺失")
                all_passed = False
        
        return all_passed
    
    def test_config_values(self, test_cases: List[Dict[str, Any]]):
        """测试配置值"""
        if not self.test_config:
            self.print_error("测试配置未加载")
            return False
        
        self.print_section("测试配置值")
        all_passed = True
        
        for test_case in test_cases:
            key_path = test_case['key']
            expected_value = test_case['expected']
            actual_value = self.config_manager.get(key_path)
            
            if actual_value == expected_value:
                self.print_success(f"配置项 {key_path}: {actual_value}")
            else:
                self.print_error(f"配置项 {key_path}: 期望 {expected_value}, 实际 {actual_value}")
                all_passed = False
        
        return all_passed
