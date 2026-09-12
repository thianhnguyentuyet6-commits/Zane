# -*- coding: utf-8 -*-
"""
OCR Real - 真实OCR - 补全
- rapidocr_onnxruntime 50MB轻量优先
- PaddleOCR 500MB可选
- 截图+OCR
"""

import os
from typing import Dict, List

class OCRReal:
    def __init__(self):
        self.engine = None
        self.engine_type = None
        
        # 优先 rapidocr_onnxruntime 50MB
        try:
            from rapidocr_onnxruntime import RapidOCR
            self.engine = RapidOCR()
            self.engine_type = "rapidocr"
            print("✅ 真实OCR可用: rapidocr_onnxruntime 50MB 轻量")
        except ImportError:
            try:
                from paddleocr import PaddleOCR
                self.engine = PaddleOCR(use_angle_cls=True, lang='ch', show_log=False)
                self.engine_type = "paddleocr"
                print("✅ 真实OCR可用: PaddleOCR 500MB")
            except ImportError:
                print("⚠️ OCR未安装，pip install rapidocr_onnxruntime (50MB轻量) 或 paddleocr (500MB)")
                self.engine = None
    
    def ocr_image(self, image_path: str) -> Dict:
        """OCR图片"""
        if not self.engine:
            return {"error": "OCR引擎不可用", "text": "", "boxes": [], "engine": "none"}
        
        try:
            if self.engine_type == "rapidocr":
                result, elapse = self.engine(image_path)
                # result: [[box, text, score], ...]
                texts = []
                boxes = []
                if result:
                    for line in result:
                        try:
                            box, text, score = line
                            texts.append(text)
                            boxes.append({"box": box, "text": text, "score": score})
                        except:
                            continue
                
                return {
                    "text": "\n".join(texts),
                    "texts": texts,
                    "boxes": boxes,
                    "count": len(texts),
                    "engine": "rapidocr_onnxruntime 50MB",
                    "elapse": elapse,
                    "real": True
                }
            elif self.engine_type == "paddleocr":
                result = self.engine.ocr(image_path, cls=True)
                texts = []
                boxes = []
                if result and result[0]:
                    for line in result[0]:
                        try:
                            box, (text, score) = line
                            texts.append(text)
                            boxes.append({"box": box, "text": text, "score": score})
                        except:
                            continue
                
                return {
                    "text": "\n".join(texts),
                    "texts": texts,
                    "boxes": boxes,
                    "count": len(texts),
                    "engine": "PaddleOCR 500MB",
                    "real": True
                }
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"error": str(e), "text": "", "boxes": [], "engine": self.engine_type}
    
    def ocr_screenshot(self) -> Dict:
        """截图+OCR"""
        try:
            from ..tools_impl import tool_executor
            screenshot = tool_executor.take_screenshot(mode="full")
            image_path = screenshot.get("image_path") or screenshot.get("path")
            
            if not image_path or not os.path.exists(image_path):
                return {"error": "截图失败", "text": ""}
            
            return self.ocr_image(image_path)
        except Exception as e:
            return {"error": str(e), "text": ""}

ocr_real = OCRReal()
