#!/usr/bin/env python3
"""
DeepWin 图像处理包整合演示
"""

import os
import sys
import cv2

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
sys.path.insert(0, project_root)

from deepwin.app_logic.memory_processing.image_processing import ImageManager
from deepwin.data_management.log_manager import LogManager
from deepwin.config.config_manager import ConfigManager

def main():
    """主函数"""
    # 初始化日志管理器
    log_manager = LogManager()
    logger = log_manager.get_logger(__name__)
    logger.info("开始图像处理演示")
    
    # 初始化配置管理器
    config_manager = ConfigManager(log_manager)
    logger.info("配置管理器初始化完成")
    
    # 创建图像管理器
    manager = ImageManager(log_manager, config_manager)
    
    # 显示可用处理器
    processors = manager.get_processor_names()
    logger.info(f"可用处理器: {processors}")
    
    # 测试人脸检测
    demo_folder = os.path.join(os.path.dirname(__file__), 'demo')
    test_image = os.path.join(demo_folder, 'demo.jpg')
    
    if os.path.exists(test_image):
        logger.info("开始测试人脸检测")
        try:
            result = manager.process_image(test_image, 'face_detection')
            if result is not None:
                info = manager.get_processor('face_detection').get_result_info()
                logger.info(f"检测结果: {info}")
                cv2.imshow("Result", result)
                cv2.waitKey(0)
                cv2.destroyAllWindows()
        except Exception as e:
            logger.error(f"测试失败: {e}")
    else:
        logger.warning(f"测试图像未找到: {test_image}")
    
    logger.info("演示完成")

if __name__ == "__main__":
    main()
