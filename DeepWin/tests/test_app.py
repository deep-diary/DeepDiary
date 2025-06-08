"""
DeepWin 应用程序测试
"""

import pytest
from PySide6.QtWidgets import QApplication
from src.core.app import DeepWinApp

@pytest.fixture
def qt_app():
    """创建 Qt 应用程序实例"""
    return QApplication([])

@pytest.fixture
def app(qt_app):
    """创建 DeepWin 应用程序实例"""
    app = DeepWinApp()
    app.set_application(qt_app)
    return app

def test_app_singleton(app):
    """测试应用程序单例模式"""
    app2 = DeepWinApp()
    assert app is app2

def test_app_properties(app):
    """测试应用程序属性"""
    assert app.app.applicationName() == "DeepWin"
    assert app.app.applicationVersion() == "0.1.0"
    assert app.app.organizationName() == "DeepDiary"
    assert app.app.organizationDomain() == "deepdiary.com" 