from .base import ImageProcessor
import easyocr
import cv2
from PIL import Image, ImageDraw, ImageFont
import numpy as np

class EasyOcrProcessor(ImageProcessor):
    def __init__(self, config_manager=None, log_manager=None):
        super().__init__(config_manager, log_manager)
        self.logger.info('EasyOcrProcessor 初始化开始')
        
        self.reader = easyocr.Reader(['en', 'ch_sim'])  # 支持中文和英文  由于初始化时间过长临时屏蔽
        self.results = None

    def reset(self):
        self.pose_data = None
        self.image = None
        self.name = None
        self.results = None

    def process(self, input_source):
        # 打开图像
        self.image, self.name = self.open(input_source)
        self.results = self.reader.readtext(self.image)
        return self.image

    def draw(self, image):
        if self.results:
            # Convert OpenCV image (BGR) to PIL image (RGB)
            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            draw = ImageDraw.Draw(pil_image)

            # Load a font that supports Chinese characters
            font_path = "C:\Windows\Fonts\simkai.ttf"  # 请替换为支持中文的字体路径
            font = ImageFont.truetype(font_path, 20)

            for (bbox, text, prob) in self.results:
                self.logger.debug(f'easyocr: {bbox}, {text}, {prob}')
                # 提取边界框的坐标
                (top_left, top_right, bottom_right, bottom_left) = bbox
                top_left = tuple(map(int, top_left))
                bottom_right = tuple(map(int, bottom_right))

                # 绘制边界框
                draw.rectangle([top_left, bottom_right], outline=(0, 0, 255), width=2)

                # 在图像上绘制文本
                draw.text((top_left[0], top_left[1] - 10), text, font=font, fill=(255, 0, 0))

            # Convert PIL image back to OpenCV image
            image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

        return image  # 保持RGB格式

    def get_result_info(self):
        return {"status": "Easy Ocr processed"}
