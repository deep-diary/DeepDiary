from .base import FolderProcessorBase
import PIL.Image as Image
import numpy as np
import os
import time
from .config_manager import ConfigManager

class CanvasProcessor(FolderProcessorBase):
    def __init__(self):
        super().__init__()
        
        # 设置默认参数
        canvas_config = self.config.get('canvas')
        if not canvas_config:
            self.config.set('canvas', 'output_folder', 'output/processed_folder/canvas')
            self.config.set('canvas', 'min_images', 20)
            self.config.set('canvas', 'target_aspect', 0.5625)
            self.config.set('canvas', 'min_width', 800)
            self.config.set('canvas', 'resize_method', 'LANCZOS')
            self.config.set('canvas', 'background_color', 'white')
        
        # 从配置文件加载参数
        self.output_folder = self.config.get('canvas', 'output_folder', 'output/processed_folder/canvas')
        self.min_images = self.config.get('canvas', 'min_images', 20)
        self.target_aspect = self.config.get('canvas', 'target_aspect', 0.5625)
        self.min_width = self.config.get('canvas', 'min_width', 800)

    def set_aspect(self, aspect_ratio):
        """设置画布长宽比"""
        self.target_aspect = aspect_ratio

    def _dp_opt(self, total_space, parts):
        """动态规划优化图片布局
        Args:
            total_space: 总空间
            parts: 各部分大小数组
        Returns:
            dp: 动态规划结果数组
            i: 使用的部分索引
            j: 使用的空间索引
            rest_space: 剩余空间
        """
        w_len = len(parts)
        dp = [[0] * (total_space + 1) for _ in range(w_len + 1)]
        i = 0
        j = 0
        for i in range(1, w_len + 1):  # parts loop
            for j in range(1, total_space + 1):  # space loop
                if parts[i - 1] <= j:
                    for k in range(0, i):  # history parts loop
                        dp[i][j] = max(max(dp[k][j - parts[i - 1]] + parts[i - 1], dp[i][j]), dp[i - 1][j])
                        if dp[i][j] == total_space:  # finish condition
                            return dp, i, j, total_space - dp[i][j]
                else:
                    dp[i][j] = dp[i - 1][j]
        return dp, i, j, total_space - dp[i][j]

    def _dp_opt_trace_back(self, dp, i, j, rest_space, w):
        """回溯动态规划结果
        Args:
            dp: 动态规划结果数组
            i: 使用的部分索引
            j: 使用的空间索引
            rest_space: 剩余空间
            w: 各部分大小数组
        Returns:
            rest_values: 未使用的部分
            used_values: 已使用的部分
            used_idx: 已使用部分的索引
        """
        w_idx = []
        j = j - rest_space
        while dp[i][j] != 0:
            rest_w = j - w[i - 1]
            is_change = False
            for k in range(0, i):
                if dp[k][rest_w] == rest_w:
                    w_idx.append(i - 1)
                    i = k
                    j = rest_w
                    is_change = True
                    break
            if not is_change:
                break

        rest_values = w.copy()
        for i in range(len(w_idx)):
            rest_values[w_idx[i]] = 0

        used_values = np.array(w)[w_idx]
        used_idx = w_idx
        return rest_values, used_values, used_idx

    def process(self, folder_path=None):
        """处理文件夹中的图片，创建画布"""
        # 检查输入文件夹
        folder_path = self.check_input_folder(folder_path)
        
        # 获取所有图片
        image_files = [f for f in os.listdir(folder_path) 
                      if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        
        total_files = len(image_files)
        print(f"\nFound {total_files} images in folder: {folder_path}")
        
        if total_files < self.min_images:
            raise ValueError(f"Need at least {self.min_images} images to create canvas")

        # 计算目标宽度和列数
        target_width = self.min_width
        step = int(pow(self.target_aspect * total_files, 0.5))
        fixed_len = target_width // step
        print(f"\nGrid size: {step} columns, {fixed_len}px per image")

        # 加载和调整图片大小
        print("\nLoading and resizing images...")
        resized_images = []
        resized_heights = []
        for idx, image_file in enumerate(image_files, 1):
            image_path = os.path.join(folder_path, image_file)
            with Image.open(image_path) as img:
                width, height = img.size
                new_width = fixed_len
                new_height = int(height * (fixed_len / width))
                resized = img.resize((new_width, new_height), Image.LANCZOS)
                resized_images.append(resized)
                resized_heights.append(new_height)
            print(f"Processed {idx}/{total_files} images", end='\r')
        print("\nAll images resized successfully")

        # 计算画布尺寸
        total_height = sum(resized_heights)
        single_col_height = total_height // step
        canvas_width = fixed_len * step
        canvas_height = single_col_height
        print(f"\nCanvas size: {canvas_width}x{canvas_height} pixels")

        # 创建画布
        canvas = Image.new('RGB', (canvas_width, canvas_height), 'white')
        
        # 使用动态规划布局图片
        print("\nOptimizing image layout...")
        w_pt = 0
        h_pt = 0
        used_img = 0
        rest_values = resized_heights.copy()

        for stp in range(step):
            dp, i, j, rest_space = self._dp_opt(single_col_height, rest_values)
            rest_values, used_values, idx = self._dp_opt_trace_back(dp, i, j, rest_space, rest_values)
            
            # 放置当前列的图片
            for img_idx in idx:
                canvas.paste(resized_images[img_idx], (w_pt, h_pt))
                h_pt += resized_heights[img_idx]
                used_img += 1
            
            # 补偿最后一张照片的误差
            if rest_space:
                img_idx = [i for i, e in enumerate(rest_values) if e != 0]
                if img_idx:
                    canvas.paste(resized_images[img_idx[0]], (w_pt, h_pt))
                    used_img += 1
            
            print(f"Column {stp + 1}/{step} completed, {used_img} images placed")
            w_pt += fixed_len
            h_pt = 0

        print(f"\nPlaced {used_img}/{total_files} images on canvas")
        if used_img < total_files:
            print(f"Warning: {total_files - used_img} images were not included")

        # 保存结果
        os.makedirs(self.output_folder, exist_ok=True)
        output_path = os.path.join(self.output_folder, 
                                 f'canvas_{time.strftime("%Y%m%d_%H%M%S")}.jpg')
        
        print(f"\nSaving canvas to: {output_path}")
        canvas.save(output_path)
        return output_path 