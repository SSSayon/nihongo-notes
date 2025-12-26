"""
配置管理模块

管理 API 配置、应用设置等
"""

from pathlib import Path
from typing import Dict, Any, List
import json
import os

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 数据目录
DATA_DIR = PROJECT_ROOT / "data"

# 文档目录
DOCS_DIR = PROJECT_ROOT / "docs"

# 配置文件路径
CONFIG_FILE = DATA_DIR / "config.json"


def load_streamlit_secrets() -> Dict[str, Any]:
    """
    加载 Streamlit secrets

    在 Streamlit 应用中运行时可以访问 st.secrets
    """
    try:
        import streamlit as st
        return dict(st.secrets)
    except:
        return {}


def load_api_configs() -> List[Dict[str, Any]]:
    """
    加载 API 配置

    优先从 Streamlit secrets 加载，否则从配置文件加载
    """
    secrets = load_streamlit_secrets()

    # 默认 API 配置
    default_configs = [
        {
            "name": "DeepSeek",
            "type": "openai",
            "url": "https://api.deepseek.com/v1/chat/completions",
            "key": secrets.get("DEEPSEEK_API_KEY", os.environ.get("DEEPSEEK_API_KEY", "")),
            "model": "deepseek-chat",
            "enabled": False,
            "priority": 1
        },
        {
            "name": "Google",
            "type": "google",
            "url": "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            "key": secrets.get("GOOGLE_API_KEY", os.environ.get("GOOGLE_API_KEY", "")),
            "model": "gemini-2.5-flash",
            "enabled": False,
            "priority": 2
        },
        {
            "name": "OpenAI",
            "type": "openai",
            "url": "https://api.openai.com/v1/chat/completions",
            "key": secrets.get("OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY", "")),
            "model": "gpt-5-mini",
            "enabled": False,
            "priority": 3
        }
    ]

    # 尝试从配置文件加载自定义设置
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved_config = json.load(f)

            # 合并配置
            saved_api_settings = saved_config.get("api_settings", {})

            ## 用 saved_config 更新默认项
            for config in default_configs:
                name = config["name"]
                saved_service = saved_api_settings.get(name, {})
                if isinstance(saved_service, dict):
                    model_settings = saved_service.get(config.get("model"))
                    if isinstance(model_settings, dict):
                        config["enabled"] = model_settings.get("enabled", config["enabled"])
                        config["priority"] = model_settings.get("priority", config["priority"])

            ## 加入 saved_config 中的新项
            for service_name, models in saved_api_settings.items():
                for model_name, settings in models.items():
                    exists = any(
                        c.get("name") == service_name and c.get("model") == model_name
                        for c in default_configs
                    )
                    if not exists:
                        new_conf = {
                            "name": service_name,
                            "type": API_TYPE_MAP.get(service_name, "openai"),
                            "url": API_URL_MAP.get(service_name, "https://api.openai.com/v1/chat/completions"),
                            "key": secrets.get(f"{service_name.upper()}_API_KEY", os.environ.get(f"{service_name.upper()}_API_KEY", "")),
                            "model": model_name,
                            "enabled": settings.get("enabled", False),
                            "priority": settings.get("priority", 999)
                        }
                        default_configs.append(new_conf)
        except:
            pass

    # 按优先级排序
    default_configs.sort(key=lambda x: x.get("priority", 999))
    return default_configs


def save_api_configs(configs: List[Dict[str, Any]]) -> bool:
    """
    保存 API 配置到配置文件

    注意：API Key 不会保存到配置文件，应保存在 secrets.toml 中
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # api_settings 结构: service -> model -> { enabled, priority }
    api_settings: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for i, cfg in enumerate(configs):
        service = cfg.get("name", "")
        model = cfg.get("model", "")
        if not service or not model:
            continue
        service_dict = api_settings.setdefault(service, {})
        service_dict[model] = {
            "enabled": cfg.get("enabled", True),
            "priority": i + 1
        }

    # 加载现有配置以保留其他字段
    existing_config = {}
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                existing_config = json.load(f)
        except:
            pass

    existing_config["api_settings"] = api_settings

    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(existing_config, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False


def get_app_settings() -> Dict[str, Any]:
    """获取应用设置"""
    default_settings = {
        "language": "zh",      # 界面语言
        "theme": "auto",       # 主题
        "items_per_page": 20,  # 每页显示条目数
        "auto_build": True,    # 保存后自动构建网站
    }

    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved_config = json.load(f)
            default_settings.update(saved_config.get("app_settings", {}))
        except:
            pass

    return default_settings


def save_app_settings(settings: Dict[str, Any]) -> bool:
    """保存应用设置"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    existing_config = {}
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                existing_config = json.load(f)
        except:
            pass

    existing_config["app_settings"] = settings

    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(existing_config, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

# api type 映射
API_TYPE_MAP = {
    "DeepSeek": "openai",
    "Google": "google",
    "OpenAI": "openai"
}
# api url 映射
API_URL_MAP = {
    "DeepSeek": "https://api.deepseek.com/v1/chat/completions",
    "Google": "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
    "OpenAI": "https://api.openai.com/v1/chat/completions"
}

# 类别配置
CATEGORIES = {
    "verbs": {
        "name": "动词",
        "icon": "🔄",
        "description": "记录动词"
    },
    "grammar": {
        "name": "语法",
        "icon": "📐",
        "description": "记录助词、句型和语法要点"
    },
    "vocabulary": {
        "name": "词汇",
        "icon": "📚",
        "description": "记录名词、形容词等词汇"
    }
}
