from setuptools import setup, find_packages

setup(
    name="deepwin",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pyserial",  # 如果使用了串口通信
    ],
) 