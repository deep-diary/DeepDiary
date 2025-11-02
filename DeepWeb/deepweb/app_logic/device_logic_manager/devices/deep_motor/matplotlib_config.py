"""
Matplotlib中文字体配置工具
提供多种解决matplotlib中文显示问题的方案
"""

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib
import platform
import os

def setup_chinese_font():
    """
    自动检测并配置中文字体
    """
    # 关闭matplotlib的调试信息
    matplotlib.set_loglevel('error')
    
    system = platform.system()
    
    if system == "Windows":
        # Windows系统字体配置
        font_list = [
            'SimHei',           # 黑体
            'Microsoft YaHei',  # 微软雅黑
            'SimSun',           # 宋体
            'KaiTi',            # 楷体
            'FangSong',         # 仿宋
            'STSong',           # 华文宋体
            'STKaiti',          # 华文楷体
            'STFangsong',       # 华文仿宋
            'STHeiti',          # 华文黑体
        ]
    elif system == "Darwin":  # macOS
        font_list = [
            'PingFang SC',      # 苹方
            'Hiragino Sans GB', # 冬青黑体
            'STHeiti',          # 华文黑体
            'Arial Unicode MS', # Arial Unicode
        ]
    else:  # Linux
        font_list = [
            'WenQuanYi Micro Hei',  # 文泉驿微米黑
            'WenQuanYi Zen Hei',    # 文泉驿正黑
            'Noto Sans CJK SC',     # Noto Sans 中文
            'Droid Sans Fallback',  # Droid Sans
        ]
    
    # 检查可用字体
    available_fonts = []
    for font in font_list:
        try:
            fm.findfont(font)
            available_fonts.append(font)
        except:
            continue
    
    if available_fonts:
        plt.rcParams['font.sans-serif'] = available_fonts + ['DejaVu Sans']
        print(f"已配置中文字体: {available_fonts[0]}")
    else:
        print("警告: 未找到合适的中文字体，将使用默认字体")
        # 尝试使用系统默认字体
        plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
    
    # 解决负号显示问题
    plt.rcParams['axes.unicode_minus'] = False

def configure_matplotlib_globally():
    """
    全局配置matplotlib，包括字体和日志级别
    在程序启动时调用一次即可
    """
    # 关闭matplotlib的调试信息
    matplotlib.set_loglevel('error')
    
    # 配置中文字体
    setup_chinese_font()
    
    # 其他全局配置
    plt.rcParams['figure.dpi'] = 100
    plt.rcParams['savefig.dpi'] = 100
    plt.rcParams['figure.autolayout'] = True
    
    print("Matplotlib全局配置完成")

def install_chinese_font():
    """
    安装中文字体（如果需要）
    """
    print("如果需要安装中文字体，请手动安装以下字体之一：")
    print("Windows: SimHei, Microsoft YaHei")
    print("macOS: PingFang SC, Hiragino Sans GB")
    print("Linux: WenQuanYi Micro Hei, Noto Sans CJK SC")

def test_chinese_display():
    """
    测试中文显示效果
    """
    setup_chinese_font()
    
    # 创建测试图表
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot([1, 2, 3, 4], [1, 4, 2, 3])
    ax.set_title('中文标题测试 - Chinese Title Test')
    ax.set_xlabel('横轴 - X Axis')
    ax.set_ylabel('纵轴 - Y Axis')
    ax.text(2, 2, '中文文本测试\nChinese Text Test', 
            fontsize=12, ha='center', va='center',
            bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue"))
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    test_chinese_display() 