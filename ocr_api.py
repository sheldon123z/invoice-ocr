#!/usr/bin/env python3
"""
统一的 OCR API 模块
支持多种视觉模型 API 提供商
"""

import base64
import json
from pathlib import Path
from typing import Optional, Dict, Any
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


class OCRAPIProvider:
    """OCR API 提供商基类"""
    
    def call_ocr(self, image_path: Path, prompt: str, timeout: int = 300) -> str:
        """调用 OCR API，返回模型响应"""
        raise NotImplementedError


class OllamaProvider(OCRAPIProvider):
    """Ollama 本地/局域网 API"""
    
    def __init__(self, host: str, port: int, model: str):
        self.host = host
        self.port = port
        self.model = model
        
    def call_ocr(self, image_path: Path, prompt: str, timeout: int = 300) -> str:
        with image_path.open("rb") as f:
            image_b64 = base64.b64encode(f.read()).decode("ascii")
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                    "images": [image_b64],
                }
            ],
            "stream": False,
        }
        
        url = f"http://{self.host}:{self.port}/api/chat"
        req = Request(url, data=json.dumps(payload).encode("utf-8"), 
                     headers={"Content-Type": "application/json"})
        
        try:
            with urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return data.get("message", {}).get("content", "")
        except Exception as e:
            raise RuntimeError(f"Ollama API 调用失败: {e}")


class VolcengineProvider(OCRAPIProvider):
    """火山引擎视觉模型 API

    注意：火山引擎使用 endpoint ID（如 ep-xxx）而不是模型名称
    在火山方舟控制台创建推理接入点后获得 endpoint ID
    API URL 是固定的：https://ark.cn-beijing.volces.com/api/v3/chat/completions
    """

    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        # 火山引擎 API URL 是固定的
        self.endpoint = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
        # model 实际是推理接入点 ID（如 ep-20251111222944-wtl8h）
        self.model = model
        
    def call_ocr(self, image_path: Path, prompt: str, timeout: int = 300) -> str:
        with image_path.open("rb") as f:
            image_b64 = base64.b64encode(f.read()).decode("ascii")
        
        # 火山引擎使用 OpenAI 兼容格式
        payload = {
            "model": self.model,  # 这里应该是 endpoint ID
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}
                        }
                    ]
                }
            ]
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        req = Request(self.endpoint, 
                     data=json.dumps(payload).encode("utf-8"),
                     headers=headers)
        
        try:
            with urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            if not content:
                raise RuntimeError(f"火山引擎返回空内容: {data}")
            return content
        except HTTPError as e:
            error_body = e.read().decode("utf-8") if hasattr(e, 'read') else str(e)
            raise RuntimeError(f"火山引擎 API HTTP错误 {e.code}: {error_body}")
        except URLError as e:
            raise RuntimeError(f"火山引擎 API 网络错误: {e.reason}")
        except Exception as e:
            raise RuntimeError(f"火山引擎 API 调用失败: {type(e).__name__}: {e}")


class OpenRouterProvider(OCRAPIProvider):
    """OpenRouter 多模型 API
    
    支持 400+ 模型，使用 OpenAI 兼容的 API 格式
    推荐设置 HTTP-Referer 和 X-Title 以在排行榜上显示
    """
    
    def __init__(self, api_key: str, model: str = "google/gemini-2.0-flash-exp:free"):
        self.api_key = api_key
        self.model = model
        self.endpoint = "https://openrouter.ai/api/v1/chat/completions"
    
    @staticmethod
    def fetch_models(api_key: str, timeout: int = 10) -> list:
        """获取OpenRouter可用模型列表
        
        返回格式: [(model_id, model_name), ...]
        例如: [("google/gemini-2.0-flash-exp:free", "Google: Gemini 2.0 Flash (free)"), ...]
        """
        url = "https://openrouter.ai/api/v1/models"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        req = Request(url, headers=headers)
        
        try:
            with urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            
            models = []
            for model in data.get("data", []):
                model_id = model.get("id", "")
                model_name = model.get("name", model_id)
                # 只添加支持视觉的模型（有context_length的通常都支持）
                if model_id and model.get("context_length", 0) > 0:
                    models.append((model_id, f"{model_name}"))
            
            # 按名称排序
            models.sort(key=lambda x: x[1])
            return models
        except HTTPError as e:
            error_body = e.read().decode("utf-8") if hasattr(e, 'read') else str(e)
            raise RuntimeError(f"获取OpenRouter模型列表失败 {e.code}: {error_body}")
        except URLError as e:
            raise RuntimeError(f"获取OpenRouter模型列表网络错误: {e.reason}")
        except Exception as e:
            raise RuntimeError(f"获取OpenRouter模型列表失败: {type(e).__name__}: {e}")
        
    def call_ocr(self, image_path: Path, prompt: str, timeout: int = 300) -> str:
        with image_path.open("rb") as f:
            image_b64 = base64.b64encode(f.read()).decode("ascii")
        
        # 检测图片类型
        image_suffix = image_path.suffix.lower()
        mime_type = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.webp': 'image/webp',
            '.gif': 'image/gif'
        }.get(image_suffix, 'image/jpeg')
        
        # OpenRouter 使用 OpenAI 兼容格式
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime_type};base64,{image_b64}"}
                        }
                    ]
                }
            ]
        }
        
        # 添加推荐的 headers 以在 OpenRouter 排行榜显示
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/sheldon123z/invoice-ocr",
            "X-Title": "Invoice OCR Tool"
        }
        
        req = Request(self.endpoint,
                     data=json.dumps(payload).encode("utf-8"),
                     headers=headers)
        
        try:
            with urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            if not content:
                raise RuntimeError(f"OpenRouter 返回空内容: {data}")
            return content
        except HTTPError as e:
            error_body = e.read().decode("utf-8") if hasattr(e, 'read') else str(e)
            raise RuntimeError(f"OpenRouter API HTTP错误 {e.code}: {error_body}")
        except URLError as e:
            raise RuntimeError(f"OpenRouter API 网络错误: {e.reason}")
        except Exception as e:
            raise RuntimeError(f"OpenRouter API 调用失败: {type(e).__name__}: {e}")


def create_provider(config: Dict[str, Any]) -> OCRAPIProvider:
    """根据配置创建 API 提供商实例"""
    provider_type = config.get("provider", "ollama")
    
    if provider_type == "ollama":
        return OllamaProvider(
            host=config.get("ollama_host", "192.168.110.219"),
            port=config.get("ollama_port", 11434),
            model=config.get("ollama_model", "qwen3-vl:8b")
        )
    elif provider_type == "volcengine":
        return VolcengineProvider(
            api_key=config.get("volcengine_api_key", ""),
            model=config.get("volcengine_model", "")
        )
    elif provider_type == "openrouter":
        return OpenRouterProvider(
            api_key=config.get("openrouter_api_key", ""),
            model=config.get("openrouter_model", "google/gemini-2.0-flash-exp:free")
        )
    else:
        raise ValueError(f"不支持的 API 提供商: {provider_type}")
