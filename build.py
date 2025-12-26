#!/usr/bin/env python3
"""
构建脚本 - 将 JSON 数据转换为 Markdown 文档

用法:
    python build.py

此脚本会读取 data/ 目录下的 JSON 数据文件，
生成对应的 Markdown 文件到 docs/ 目录。
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

from app.config import CATEGORIES

# 项目路径
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
DOCS_DIR = PROJECT_ROOT / "docs"


def load_json(file_path: Path) -> list:
    """加载 JSON 文件"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"警告: 无法加载 {file_path}: {e}")
        return []

def _build_examples_section(examples: list) -> list:
    """构建例句部分的 Markdown"""
    lines = []
    if examples:
        lines.append("- **例句**：")
        lines.append("")
        for ex in examples:
            html_text = ex.get("html", ex.get("jp", ""))
            cn = ex.get("cn", "")
            lines.append('    > <div class="example-box">')
            lines.append(f"    > {html_text}")
            lines.append(f"    > <br><small>{cn}</small>")
            lines.append("    > </div>")
            lines.append("")
    return lines

def _build_notes_section(notes: str) -> list:
    """构建备注部分的 Markdown"""
    lines = []
    if notes:
        lines.append(f"> 📝 **备注**：")
        lines.append("")
        for line in notes.splitlines():
            lines.append(f"> {line}")
            lines.append("> ")
        lines.append("")
    return lines

def build_verbs_page(data: list) -> str:
    """构建动词页面"""
    lines = [
        "# 🔄 动词",
        "",
        f"{CATEGORIES['verbs']['description']}。",
        "",
        f"共 **{len(data)}** 个动词",
        "",
        "---",
        ""
    ]

    if not data:
        lines.append("暂无数据。")
        return "\n".join(lines)

    for item in data:
        display = item.get("word", item.get("reading", ""))
        reading = f"{item.get('display_html', '')}（{item.get('reading', '')}）"
        verb_type = item.get("type", "")
        meaning = item.get("meaning", "")

        lines.append(f"## {display}")
        lines.append("")
        lines.append(f"- **读音**：{reading}")
        lines.append(f"- **类型**：{verb_type}")
        lines.append(f"- **释义**：{meaning}")
        lines.append("")

        examples = item.get("examples", [])
        lines.extend(_build_examples_section(examples))

        notes = item.get("notes", "")
        lines.extend(_build_notes_section(notes))

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def build_grammar_page(data: list) -> str:
    """构建语法页面"""
    lines = [
        "# 📐 语法",
        "",
        f"{CATEGORIES['grammar']['description']}。",
        "",
        f"共 **{len(data)}** 条语法",
        "",
        "---",
        ""
    ]

    if not data:
        lines.append("暂无数据。")
        return "\n".join(lines)

    for item in data:
        display = item.get("title", item.get("display_html", ""))
        category = item.get("category", "")
        meaning = item.get("meaning", "")

        lines.append(f"## {display}")
        lines.append("")
        lines.append(f"- **类别**：{category}")
        lines.append(f"- **含义**：{meaning}")
        lines.append("")

        usage = item.get("usage", [])
        if usage:
            lines.append("- **用法**：")
            lines.append("")
            for u in usage:
                lines.append(f"    - {u}")
            lines.append("")

        examples = item.get("examples", [])
        lines.extend(_build_examples_section(examples))

        notes = item.get("notes", "")
        lines.extend(_build_notes_section(notes))

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def build_vocabulary_page(data: list) -> str:
    """构建词汇页面"""
    lines = [
        "# 📚 词汇",
        "",
        f"{CATEGORIES['vocabulary']['description']}。",
        "",
        f"共 **{len(data)}** 个词汇",
        "",
        "---",
        ""
    ]

    if not data:
        lines.append("暂无数据。")
        return "\n".join(lines)

    for item in data:
        display = item.get("word", item.get("reading", ""))
        reading = f"{item.get('display_html', '')}（{item.get('reading', '')}）"
        word_type = item.get("type", "")
        meaning = item.get("meaning", "")

        lines.append(f"## {display}")
        lines.append("")
        lines.append(f"- **读音**：{reading}")
        lines.append(f"- **词性**：{word_type}")
        lines.append(f"- **释义**：{meaning}")
        lines.append("")

        examples = item.get("examples", [])
        lines.extend(_build_examples_section(examples))

        notes = item.get("notes", "")
        lines.extend(_build_notes_section(notes))

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def build_index_page(stats: dict) -> str:
    """构建首页"""
    total = sum(stats.values())
    now = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M")

    content = f"""# 日语笔记

## 📊 内容统计

| 类别 | 数量 |
|------|------|
| 🔄 动词 | {stats.get('verbs', 0)} |
| 📐 语法 | {stats.get('grammar', 0)} |
| 📚 词汇 | {stats.get('vocabulary', 0)} |
| **总计** | **{total}** |

<p><small style="color:#6b7280">最后更新: {now} (UTC+8)</small></p>
"""
    return content


def main():
    """主函数"""
    print("📚 开始构建日语笔记...")

    # 确保目录存在
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    # 加载数据
    verbs = load_json(DATA_DIR / "verbs.json")
    grammar = load_json(DATA_DIR / "grammar.json")
    vocabulary = load_json(DATA_DIR / "vocabulary.json")

    stats = {
        "verbs": len(verbs),
        "grammar": len(grammar),
        "vocabulary": len(vocabulary)
    }

    # 构建页面
    pages = {
        "index.md": build_index_page(stats),
        "verbs.md": build_verbs_page(verbs),
        "grammar.md": build_grammar_page(grammar),
        "vocabulary.md": build_vocabulary_page(vocabulary)
    }

    # 写入文件
    for filename, content in pages.items():
        file_path = DOCS_DIR / filename
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  ✓ {filename}")

    print(f"\n✅ 构建完成！")
    print(f"   动词: {stats['verbs']} 条")
    print(f"   语法: {stats['grammar']} 条")
    print(f"   词汇: {stats['vocabulary']} 条")
    print(f"\n运行 'mkdocs serve' 预览网站")


if __name__ == "__main__":
    main()
