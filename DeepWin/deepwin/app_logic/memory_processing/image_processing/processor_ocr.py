import os
from .base import ImageProcessor
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from PIL import Image

class OcrProcessor(ImageProcessor):
    def __init__(self, config_manager=None, log_manager=None):
        super().__init__(config_manager, log_manager)
        self.logger.info('OcrProcessor 初始化开始')

        # 禁用代理
        os.environ['HTTP_PROXY'] = ''
        os.environ['HTTPS_PROXY'] = ''

        # try:
        #     self.ocr_processor = TrOCRProcessor.from_pretrained('microsoft/trocr-base-handwritten')
        #     self.ocr_model = VisionEncoderDecoderModel.from_pretrained('microsoft/trocr-base-handwritten')
        # except Exception as e:
        #     print(f"Error loading TrOCRProcessor: {e}")
            # 处理加载失败的情况，例如使用本地模型
        

        self.results = None

    def reset(self):
        self.pose_data = None
        self.image = None
        self.name = None
        self.results = None

    def process(self, input_source):
        # 打开图像
        # self.image, self.name = self.open(input_source)
        
 
        image = Image.open('image_processing/demo/ocr.png')
        pixel_values = self.ocr_processor(self.image, return_tensors="pt").pixel_values

        generated_ids = self.ocr_model.generate(pixel_values)
        generated_text = self.ocr_processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        self.logger.info(f"OCR识别结果: {generated_text}")

    def draw(self, image):
        
        return image  # 保持RGB格式

    def get_result_info(self):
        return {"status": "Ocr processed"}
