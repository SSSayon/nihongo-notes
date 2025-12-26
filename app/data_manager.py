"""
数据管理模块

负责：
- 读取/写入 JSON 数据文件
- 数据去重与合并
- 按时间排序
- 增删改查操作
"""

import json
import os
import time
from typing import List, Dict, Any, Optional
from pathlib import Path

import pykakasi

# 数据文件路径
DATA_DIR = Path(__file__).parent.parent / "data"

DATA_FILES = {
    "verbs": DATA_DIR / "verbs.json",
    "grammar": DATA_DIR / "grammar.json",
    "vocabulary": DATA_DIR / "vocabulary.json"
}


def ensure_data_dir():
    """确保数据目录存在"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # 确保每个数据文件都存在
    for file_path in DATA_FILES.values():
        if not file_path.exists():
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False)


def load_data(category: str) -> List[Dict[str, Any]]:
    """
    加载指定类别的数据

    Args:
        category: 数据类别 (verbs/grammar/vocabulary)

    Returns:
        数据列表
    """
    ensure_data_dir()

    if category not in DATA_FILES:
        raise ValueError(f"未知的数据类别: {category}")

    file_path = DATA_FILES[category]

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def save_data(category: str, data: List[Dict[str, Any]]) -> bool:
    """
    保存数据到指定类别的文件

    Args:
        category: 数据类别
        data: 要保存的数据列表

    Returns:
        是否保存成功
    """
    ensure_data_dir()

    if category not in DATA_FILES:
        raise ValueError(f"未知的数据类别: {category}")

    file_path = DATA_FILES[category]

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存数据失败: {e}")
        return False


def add_items(category: str, new_items: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    添加新条目

    Args:
        category: 数据类别
        new_items: 新条目列表

    Returns:
        操作结果统计 {"added": n, "updated": m}
    """
    existing_data = load_data(category)

    added = 0

    for item in new_items:
        # 确保有时间戳
        if not item.get("created_at"):
            item["created_at"] = int(time.time())

        existing_data.append(item)
        added += 1

    # 倒序排序，最新的在前面
    existing_data.sort(key=lambda x: x.get("created_at", 0), reverse=True)

    save_data(category, existing_data)

    return {"added": added}


def delete_items(category: str, item_ids: List[str]) -> int:
    """
    删除指定条目

    Args:
        category: 数据类别
        item_ids: 要删除的条目 ID 列表

    Returns:
        实际删除的条目数量
    """
    existing_data = load_data(category)
    original_count = len(existing_data)

    # 过滤掉要删除的条目
    existing_data = [item for item in existing_data if item.get("id") not in item_ids]

    deleted_count = original_count - len(existing_data)

    if deleted_count > 0:
        save_data(category, existing_data)

    return deleted_count


def update_item(category: str, item_id: str, updates: Dict[str, Any]) -> bool:
    """
    更新指定条目

    Args:
        category: 数据类别
        item_id: 要更新的条目 ID
        updates: 更新内容字典

    Returns:
        是否更新成功
    """
    existing_data = load_data(category)
    updated = False

    for item in existing_data:
        if item.get("id") == item_id:
            item.update(updates)
            updated = True
            break

    if updated:
        save_data(category, existing_data)

    return updated


def get_statistics() -> Dict[str, int]:
    """获取数据统计"""
    return {
        category: len(load_data(category))
        for category in DATA_FILES.keys()
    }


def generate_id(word: str, convert: bool = True) -> str:
    """
    根据单词生成唯一 ID

    将日文转换为罗马字拼音作为 ID
    """

    if not convert:
        return f"{word}_{int(time.time())}"

    kks = pykakasi.kakasi()
    result = ""
    for item in kks.convert(word):
        result += item['hepburn']

    return f"{result}_{int(time.time())}"
