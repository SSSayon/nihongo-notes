"""
LLM 客户端模块 - 统一调用不同 LLM API

"""

import json
import random
import requests
from typing import Optional, Dict, Any, List


class LLMClient:
    """统一的 LLM 客户端"""

    # API 类型常量
    TYPE_OPENAI = "openai"
    TYPE_GOOGLE = "google"
    TYPE_ANTHROPIC = "anthropic"

    def __init__(self, api_configs: List[Dict[str, Any]]):
        """
        初始化 LLM 客户端

        Args:
            api_configs: API 配置列表，按优先级排序
                每个配置包含:
                - name: API 名称 (显示用)
                - type: API 类型 (openai/google/anthropic)
                - url: API 端点 URL
                - key: API Key
                - model: 模型名称
                - enabled: 是否启用 (可选，默认 True)
        """
        self.api_configs = api_configs
        self.last_used_api = None
        self.last_error = None

    def call(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        """
        调用 LLM API，自动故障转移

        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词 (可选)

        Returns:
            LLM 响应文本，如果全部失败则返回 None
        """
        enabled_configs = [c for c in self.api_configs if c.get("enabled", True)]

        for config in enabled_configs:
            try:
                result = self._call_single_api(config, prompt, system_prompt)
                if result:
                    self.last_used_api = f"{config['name']} - {config['model']}"
                    self.last_error = None
                    return result
            except Exception as e:
                self.last_error = f"{config['name']} - {config['model']}: {str(e)}"
                print(f"[LLM] {config['name']} - {config['model']} 调用失败: {e}")
                continue

        return None

    def _call_single_api(
        self,
        config: Dict[str, Any],
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> Optional[str]:
        """调用单个 API"""

        api_type = config.get("type", self.TYPE_OPENAI)

        if api_type == self.TYPE_OPENAI:
            return self._call_openai_style(config, prompt, system_prompt)
        elif api_type == self.TYPE_GOOGLE:
            return self._call_google(config, prompt, system_prompt)
        else:
            raise ValueError(f"不支持的 API 类型: {api_type}")

    def _call_openai_style(
        self,
        config: Dict[str, Any],
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> Optional[str]:
        """调用 OpenAI 风格的 API (包括兼容接口)"""

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config['key']}"
        }

        payload = {
            "model": config.get("model", "gpt-5-mini"),
            "messages": messages,
            "temperature": self._set_temperature(config),
        }

        response = requests.post(
            config["url"],
            headers=headers,
            json=payload,
            timeout=60
        )

        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}: {response.text}")

        data = response.json()
        return data["choices"][0]["message"]["content"]

    def _call_google(
        self,
        config: Dict[str, Any],
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> Optional[str]:
        """调用 Google Gemini API"""

        # Google Gemini API 格式
        config["url"] = config["url"].format(model=config.get("model", "gemini-3-flash-preview"))
        url = f"{config['url']}?key={config['key']}"

        contents = []
        if system_prompt:
            contents.append({
                "role": "user",
                "parts": [{"text": f"System: {system_prompt}"}]
            })
            contents.append({
                "role": "model",
                "parts": [{"text": "Understood. I will follow these instructions."}]
            })

        contents.append({
            "role": "user",
            "parts": [{"text": prompt}]
        })

        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": self._set_temperature(config),
            }
        }

        response = requests.post(url, headers=headers, json=payload, timeout=60)

        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}: {response.text}")

        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]

    def _set_temperature(self, config: Dict[str, Any], base: float = 0.6) -> float:
        """设置温度参数"""
        return config.get("temperature", base + random.random() * 0.1)

    def parse_json_response(self, response: str) -> Optional[Any]:
        """
        从 LLM 响应中解析 JSON

        LLM 可能会在 JSON 前后添加说明文字，此函数尝试提取有效的 JSON。
        """
        if not response:
            return None

        # 尝试直接解析
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # 尝试提取 ```json ... ``` 代码块
        import re
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', response)
        if json_match:
            try:
                return json.loads(json_match.group(1).strip())
            except json.JSONDecodeError:
                pass

        # 尝试提取 [ ... ] 或 { ... }
        for pattern in [r'\[[\s\S]*\]', r'\{[\s\S]*\}']:
            match = re.search(pattern, response)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    continue

        return None
