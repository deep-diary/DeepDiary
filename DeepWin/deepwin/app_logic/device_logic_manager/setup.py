from setuptools import setup, find_packages

setup(
    name="device_logic_manager",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'pyserial',
        'pyyaml'
    ],
    python_requires='>=3.6',
    author="BlueDoc",
    description="Device Logic Manager for DeepWin",
    package_data={
        'protocol_processing': ['devices/deep_arm/config.yaml'],
    },
) 