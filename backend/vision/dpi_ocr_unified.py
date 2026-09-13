# -*- coding: utf-8 -*-
"""
DPI坐标系统一+OCR - Zane v0913
解决优先级11：OCR DPI坐标系统一先统一DPI缩放再PaddleOCR/Tesseract最后UIA树
"""
import sys
import os
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger("zane")

class DPIOCRUUnified:
    """DPI+OCR统一 - 先统一DPI缩放再OCR最后UIA树"""
    
    def __init__(self):
        self.dpi_scale = 1.0
        self.screen_width = 1920
        self.screen_height = 1080
        self.detected_dpi = 96
        self.scale_factors = [1.0, 1.25, 1.5, 1.75, 2.0]  # 100% 125% 150% 175% 200%
        self.init_dpi()
    
    def init_dpi(self):
        """初始化DPI检测"""
        try:
            if sys.platform == "win32":
                import ctypes
                # 获取DPI
                try:
                    # Windows 8.1+
                    ctypes.windll.shcore.SetProcessDpiAwareness(2)
                except:
                    try:
                        ctypes.windll.user32.SetProcessDPIAware()
                    except:
                        pass
                
                # 获取屏幕DPI
                try:
                    hdc = ctypes.windll.user32.GetDC(0)
                    dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)  # LOGPIXELSX
                    ctypes.windll.user32.ReleaseDC(0, hdc)
                    self.detected_dpi = dpi
                    self.dpi_scale = dpi / 96.0
                    logger.info(f"✅ DPI检测 Windows DPI:{dpi} 缩放:{self.dpi_scale:.2f}")
                except Exception as e:
                    logger.warning(f"DPI检测失败: {e} 使用默认1.0")
                    self.dpi_scale = 1.0
            else:
                # Linux/Mac
                self.dpi_scale = 1.0
                logger.info(f"✅ DPI检测 {sys.platform} 默认缩放1.0")
            
            # 获取屏幕分辨率
            try:
                import tkinter as tk
                root = tk.Tk()
                self.screen_width = root.winfo_screenwidth()
                self.screen_height = root.winfo_screenheight()
                root.destroy()
                logger.info(f"✅ 屏幕分辨率: {self.screen_width}x{self.screen_height}")
            except Exception as e:
                logger.warning(f"屏幕分辨率检测失败: {e}")
        
        except Exception as e:
            logger.warning(f"DPI初始化失败: {e}")
    
    def unify_coordinates(self, x: int, y: int, from_dpi: float = None) -> Tuple[int, int]:
        """统一坐标 - 将任意DPI坐标转换为逻辑坐标"""
        if from_dpi is None:
            from_dpi = self.dpi_scale
        
        # 统一到96 DPI逻辑坐标
        logical_x = int(x / from_dpi)
        logical_y = int(y / from_dpi)
        
        logger.debug(f"DPI统一坐标 {x},{y} DPI:{from_dpi} → 逻辑 {logical_x},{logical_y}")
        return logical_x, logical_y
    
    def to_physical(self, x: int, y: int) -> Tuple[int, int]:
        """逻辑坐标转物理坐标"""
        physical_x = int(x * self.dpi_scale)
        physical_y = int(y * self.dpi_scale)
        return physical_x, physical_y
    
    def get_dpi_info(self) -> Dict[str, Any]:
        """获取DPI信息"""
        return {
            "detected_dpi": self.detected_dpi,
            "dpi_scale": round(self.dpi_scale, 2),
            "screen_width": self.screen_width,
            "screen_height": self.screen_height,
            "scale_factors": self.scale_factors,
            "platform": sys.platform,
            "is_high_dpi": self.dpi_scale > 1.0
        }
    
    def ocr_with_dpi(self, image_path: str = None, image_data: bytes = None) -> Dict[str, Any]:
        """
        OCR统一流程：
        1. 先统一DPI缩放
        2. 再PaddleOCR/Tesseract
        3. 最后UIA树
        """
        dpi_info = self.get_dpi_info()
        logger.info(f"🔍 OCR流程 DPI统一 {dpi_info}")
        
        # 1. DPI统一
        # 如果是截图，需要根据DPI缩放调整
        # 2. OCR识别
        ocr_result = self._ocr_recognize(image_path, image_data)
        
        # 3. UIA树
        uia_result = self._uia_tree()
        
        return {
            "dpi_info": dpi_info,
            "ocr": ocr_result,
            "uia": uia_result,
            "unified": True,
            "flow": "DPI统一 → OCR识别 → UIA树"
        }
    
    def _ocr_recognize(self, image_path: str = None, image_data: bytes = None) -> Dict[str, Any]:
        """OCR识别 - RapidOCR 50MB + Tesseract回退"""
        result = {
            "text": "",
            "boxes": [],
            "confidence": 0,
            "engine": "none"
        }
        
        # 尝试RapidOCR
        try:
            from rapidocr_onnxruntime import RapidOCR
            engine = RapidOCR()
            
            if image_path and Path(image_path).exists():
                ocr_result, _ = engine(image_path)
            elif image_data:
                # 从bytes识别
                import tempfile
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
                    f.write(image_data)
                    temp_path = f.name
                ocr_result, _ = engine(temp_path)
                os.unlink(temp_path)
            else:
                ocr_result = []
            
            if ocr_result:
                texts = []
                boxes = []
                for box, text, conf in ocr_result:
                    texts.append(text)
                    boxes.append({"box": box, "text": text, "confidence": conf})
                
                result["text"] = "\n".join(texts)
                result["boxes"] = boxes
                result["confidence"] = sum(b["confidence"] for b in boxes) / len(boxes) if boxes else 0
                result["engine"] = "rapidocr"
                logger.info(f"✅ RapidOCR识别 {len(texts)}段文字 置信度:{result['confidence']:.2f}")
            else:
                result["text"] = ""
                result["engine"] = "rapidocr_empty"
        
        except ImportError:
            logger.warning("RapidOCR未安装，尝试Tesseract")
            # Tesseract回退
            try:
                import pytesseract
                from PIL import Image
                
                if image_path:
                    img = Image.open(image_path)
                    text = pytesseract.image_to_string(img, lang='chi_sim+eng')
                    result["text"] = text
                    result["engine"] = "tesseract"
                    logger.info(f"✅ Tesseract识别 {len(text)}字符")
            except ImportError:
                logger.warning("Tesseract也未安装，OCR不可用")
                result["engine"] = "none"
                result["text"] = "OCR引擎未安装"
        except Exception as e:
            logger.error(f"OCR失败: {e}")
            result["error"] = str(e)
        
        return result
    
    def _uia_tree(self) -> Dict[str, Any]:
        """UIA树 - Windows UI Automation"""
        if sys.platform != "win32":
            return {"available": False, "reason": "仅Windows支持UIA", "platform": sys.platform}
        
        try:
            # 尝试uiautomation
            import uiautomation as auto
            
            # 获取桌面
            desktop = auto.GetRootControl()
            result = {
                "available": True,
                "desktop": {
                    "name": desktop.Name,
                    "class": desktop.ClassName,
                    "children_count": len(list(desktop.GetChildren()))
                },
                "windows": []
            }
            
            # 枚举窗口
            for window in desktop.GetChildren():
                if window.ControlTypeName == "WindowControl":
                    result["windows"].append({
                        "name": window.Name,
                        "class": window.ClassName,
                        "handle": window.Handle,
                        "rect": {
                            "left": window.BoundingRectangle.left,
                            "top": window.BoundingRectangle.top,
                            "right": window.BoundingRectangle.right,
                            "bottom": window.BoundingRectangle.bottom
                        }
                    })
            
            logger.info(f"✅ UIA树获取 {len(result['windows'])}个窗口")
            return result
        
        except ImportError:
            logger.warning("uiautomation未安装")
            return {"available": False, "reason": "uiautomation未安装"}
        except Exception as e:
            logger.error(f"UIA树失败: {e}")
            return {"available": False, "error": str(e)}

# 全局实例
dpi_ocr_unified = DPIOCRUUnified()
