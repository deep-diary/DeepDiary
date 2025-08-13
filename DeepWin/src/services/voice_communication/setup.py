from setuptools import setup, find_packages
import os

# 读取README文件作为长描述
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "Voice Communication Package for DeepWin"

# 读取requirements.txt文件
def read_requirements():
    req_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if os.path.exists(req_path):
        with open(req_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

# 获取版本信息
def get_version():
    version_file = os.path.join(os.path.dirname(__file__), '__init__.py')
    if os.path.exists(version_file):
        with open(version_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('__version__'):
                    return line.split('=')[1].strip().strip('"\'')
    return "0.1.1"

setup(
    name="voice_communication",
    version=get_version(),
    description="Voice Communication Package for DeepWin - Support text dialogue, transcription, VQA, live video streaming",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    
    # 作者信息
    author="DeepWin Team",
    author_email="team@deepwin.com",
    url="https://github.com/deepwin/DeepWin",
    
    # 包配置 - 修复这里！
    py_modules=[],  # 空列表，因为这是一个包而不是单个模块
    packages=[''],  # 空字符串表示当前目录作为包
    
    # 包含数据文件
    include_package_data=True,
    package_data={
        '': [  # 空字符串表示当前目录
            '*.py',
            '*.md',
            '*.txt',
            '*.jpg',
            '*.wav'
        ]
    },
    
    # 安装依赖
    install_requires=read_requirements(),
    
    # 额外依赖
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-qt>=4.0.0',
            'black>=22.0.0',
            'flake8>=4.0.0',
            'mypy>=0.950'
        ],
        'full': [
            'opencv-python>=4.5.0',
            'numpy>=1.21.0',
            'Pillow>=8.0.0',
            'sounddevice>=0.4.0',
            'python-json-logger>=2.0.7'
        ]
    },
    
    # Python版本要求
    python_requires=">=3.8",
    
    # 分类信息
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Multimedia :: Sound/Audio",
        "Topic :: Multimedia :: Video",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    
    # 关键词
    keywords="voice communication, speech recognition, text-to-speech, vqa, video streaming, deepwin",
    
    # 项目URLs
    project_urls={
        "Bug Reports": "https://github.com/deepwin/DeepWin/issues",
        "Source": "https://github.com/deepwin/DeepWin",
        "Documentation": "https://github.com/deepwin/DeepWin/docs",
    },
    
    # 入口点
    entry_points={
        'console_scripts': [
            'deepwin-voice=voice_communication.example_usage:main',
            'deepwin-vqa=voice_communication.run_vqa:main',
            'deepwin-live=voice_communication.run_live_ai:main',
        ],
    },
    
    # 依赖链接
    dependency_links=[],
    
    # 平台特定配置
    zip_safe=False,
    
    # 包含许可证
    license="MIT",
)