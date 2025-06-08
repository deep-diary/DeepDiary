from setuptools import setup, find_namespace_packages

setup(
    name="deepwin",
    version="0.1.0",
    packages=find_namespace_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "PySide6>=6.6.0",
        "PySide6-Fluent-Widgets>=1.4.0",
        "loguru>=0.7.0",
    ],
    python_requires=">=3.10",
) 