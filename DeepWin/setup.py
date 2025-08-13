from setuptools import setup, find_packages
import os

# 读取README文件
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

setup(
    name="deepwin",
    version="0.1.0",
    author="DeepDiary Team",
    description="DeepWin - AI-powered device management system",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    # 修改这里：直接使用 find_packages() 而不是 find_packages(where="src")
    packages=find_packages(),
    # 删除 package_dir 配置
    # package_dir={"": "src"},
    install_requires=[
        "PySide6>=6.6.0",
        "PySide6-Fluent-Widgets>=1.4.0",
        "loguru>=0.7.0",
    ],
    python_requires=">=3.10",
    include_package_data=True,
    package_data={
        "": ["*.py", "*.md", "*.txt", "*.json", "*.qss", "*.qm", "*.ts"],
    },
    extras_require={
        'dev': ['pytest', 'black', 'flake8'],
        'test': ['pytest', 'pytest-cov'],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)

# 使用流程
# 开发阶段：使用 pip install -e . 进行开发模式安装
# 测试阶段：使用 python setup.py test 或 pytest 运行测试
# 发布阶段：使用 python setup.py sdist bdist_wheel 构建分发包
# 部署阶段：使用 pip install package_name 安装到目标环境
# 这样的配置可以让你的 DeepWin 包更容易安装、分发和维护。