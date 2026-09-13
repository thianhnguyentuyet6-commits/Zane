# -*- coding: utf-8 -*-
"""
真实OCR v0914 - RapidOCR延迟下载，首次调用检测缓存询问用户
- 不放进主安装脚本强制下载，减轻新用户第一次安装负担
- 首次调用时检测本地缓存，没有则询问用户是否下载
"""
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

class OCRRealV0914:
    """真实OCR v0914 - 延迟下载"""
    
    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir or os.path.join(os.path.dirname(__file__), "..", "..")).resolve()
        self.models_dir = self.base_dir / "data" / "models" / "rapidocr"
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        self.rapidocr_available = False
        self.tesseract_available = False
        self.ocr_engine = None
        
        # 检测可用性，但不强制下载
        self._check_availability()
    
    def _check_availability(self):
        """检查OCR可用性，不强制下载"""
        try:
            import rapidocr_onnxruntime
            self.rapidocr_available = True
        except ImportError:
            self.rapidocr_available = False
        
        try:
            import pytesseract
            self.tesseract_available = True
        except ImportError:
            self.tesseract_available = False
    
    def _check_models_cached(self) -> Dict[str, Any]:
        """检查模型是否已缓存"""
        # RapidOCR模型通常在第一次使用时自动下载到缓存
        # 检查常见缓存位置
        cache_locations = [
            self.models_dir,
            Path.home() / ".cache" / "rapidocr",
            Path.home() / ".rapidocr",
            self.base_dir / "models" / "rapidocr"
        ]
        
        cached = False
        cache_path = None
        model_files = []
        
        for loc in cache_locations:
            if loc.exists():
                # 检查是否有模型文件
                files = list(loc.glob("*.onnx")) + list(loc.glob("*.yaml")) + list(loc.glob("*.json"))
                if files:
                    cached = True
                    cache_path = loc
                    model_files = files[:5]  # 前5个
                    break
        
        return {
            "cached": cached,
            "cache_path": str(cache_path) if cache_path else None,
            "model_files": [str(f) for f in model_files],
            "cache_locations": [str(loc) for loc in cache_locations],
            "rapidocr_available": self.rapidocr_available,
            "tesseract_available": self.tesseract_available
        }
    
    def _prompt_download(self) -> Dict[str, Any]:
        """询问用户是否下载模型"""
        cache_info = self._check_models_cached()
        
        if cache_info["cached"]:
            return {
                "need_download": False,
                "cached": True,
                "message": f"OCR模型已缓存：{cache_info['cache_path']}",
                "cache_info": cache_info
            }
        
        # 未缓存，询问用户
        return {
            "need_download": True,
            "cached": False,
            "message": "OCR模型未缓存，首次使用需下载约50MB模型文件",
            "prompt": "是否下载RapidOCR模型？(约50MB，首次使用)",
            "download_size": "~50MB",
            "cache_info": cache_info,
            "download_command": "pip install rapidocr_onnxruntime -U",
            "note": "RapidOCR模型首次调用时自动下载，不强制包含在主安装中，减轻新用户负担",
            "options": {
                "yes": "下载模型，启用真实OCR",
                "no": "暂不下载，使用演示OCR",
                "tesseract": "使用Tesseract替代（需系统安装tesseract）"
            }
        }
    
    def get_ocr_engine(self, allow_download: bool = False) -> Optional[Any]:
        """获取OCR引擎，支持延迟下载"""
        if self.ocr_engine:
            return self.ocr_engine
        
        # 检查缓存
        cache_info = self._check_models_cached()
        
        # 如果未缓存且不允许下载，返回None
        if not cache_info["cached"] and not allow_download:
            # 检查是否有Tesseract作为替代
            if self.tesseract_available:
                try:
                    import pytesseract
                    self.ocr_engine = "tesseract"
                    return self.ocr_engine
                except Exception:
                    pass
            return None
        
        # 尝试加载RapidOCR
        if self.rapidocr_available:
            try:
                from rapidocr_onnxruntime import RapidOCR
                # 首次调用会自动下载模型
                self.ocr_engine = RapidOCR()
                return self.ocr_engine
            except Exception as e:
                print(f"RapidOCR加载失败: {e}")
                # 回退Tesseract
                if self.tesseract_available:
                    try:
                        import pytesseract
                        self.ocr_engine = "tesseract"
                        return self.ocr_engine
                    except Exception:
                        pass
        
        # 回退Tesseract
        if self.tesseract_available:
            try:
                import pytesseract
                self.ocr_engine = "tesseract"
                return self.ocr_engine
            except Exception:
                pass
        
        return None
    
    def ocr_image(self, image_path: str, allow_download: bool = False) -> Dict[str, Any]:
        """OCR识别 - 延迟下载"""
        # 检查是否需要下载
        prompt_info = self._prompt_download()
        
        if prompt_info["need_download"] and not allow_download:
            return {
                "success": False,
                "need_download": True,
                "prompt_info": prompt_info,
                "message": prompt_info["message"],
                "demo_fallback": True,
                "text": "演示OCR文本 - 需下载模型启用真实OCR",
                "note": "首次调用检测到模型未缓存，询问用户是否下载，不强制"
            }
        
        # 尝试真实OCR
        engine = self.get_ocr_engine(allow_download=allow_download)
        
        if not engine:
            return {
                "success": False,
                "error": "OCR引擎不可用",
                "prompt_info": prompt_info,
                "demo_fallback": True,
                "text": "演示OCR - 引擎不可用",
                "install_help": "pip install rapidocr_onnxruntime -U 或安装Tesseract"
            }
        
        try:
            if engine == "tesseract":
                import pytesseract
                from PIL import Image
                img = Image.open(image_path)
                text = pytesseract.image_to_string(img, lang='chi_sim+eng')
                return {
                    "success": True,
                    "text": text,
                    "engine": "tesseract",
                    "image_path": image_path,
                    "demo_mode": False
                }
            else:
                # RapidOCR
                result, _ = engine(image_path)
                if result:
                    text = "\n".join([line[1] for line in result])
                    blocks = [
                        {"text": line[1], "confidence": line[2], "box": line[0]}
                        for line in result
                    ]
                    return {
                        "success": True,
                        "text": text,
                        "blocks": blocks,
                        "engine": "rapidocr",
                        "image_path": image_path,
                        "demo_mode": False,
                        "model_cached": True
                    }
                else:
                    return {
                        "success": True,
                        "text": "",
                        "blocks": [],
                        "engine": "rapidocr",
                        "image_path": image_path,
                        "demo_mode": False,
                        "note": "未识别到文字"
                    }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "engine": str(engine),
                "image_path": image_path,
                "demo_fallback": True,
                "text": f"OCR失败演示文本: {e}",
                "prompt_info": prompt_info
            }
    
    def get_status(self) -> Dict[str, Any]:
        """获取OCR状态"""
        cache_info = self._check_models_cached()
        prompt_info = self._prompt_download()
        
        return {
            "rapidocr_available": self.rapidocr_available,
            "tesseract_available": self.tesseract_available,
            "engine_loaded": self.ocr_engine is not None,
            "cache_info": cache_info,
            "prompt_info": prompt_info,
            "models_dir": str(self.models_dir),
            "note": "首次调用检测缓存，没有则询问用户是否下载，不强制"
        }


# 全局 v0914
ocr_real = OCRRealV0914()
# 兼容
ocr_real_v0914 = ocr_real
