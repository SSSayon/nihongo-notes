"""
Prompt 模板模块

定义用于调用 LLM 的提示词模板
"""

# 系统提示词
SYSTEM_PROMPT = """你是一个专业的日语教学助手。你的任务是帮助用户整理日语学习笔记。

你需要：
1. 将用户输入的日语词汇/语法转换为标准格式。如果用户输入的不是原形，需要还原为原形
2. 为**所有**汉字添加假名注音（使用 HTML <ruby> 标签）
3. 输出必须是有效的 JSON 格式

关于注音规则：
- 对于汉字，使用 <ruby>汉字<rt>假名</rt></ruby> 格式，例如："食べる" → "<ruby>食<rt>た</rt></ruby>べる"
- 对于纯假名，直接输出假名

请确保：
- 例句要贴近日常生活、实用性强，若词汇有多个含义则应分别提供例句，同类例句不应重复
- 语法解释要简洁清晰
"""


def get_verb_prompt(words: str) -> str:
    """获取动词生成提示词"""
    return f"""请将以下日语动词整理为标准格式。每个动词需要包含：
- id: 唯一标识（使用动词的罗马字读音）
- word: 动词原形
- reading: 假名读音
- display_html: 带注音的 HTML 格式
- type: 动词类型（五段动词/一段动词/サ变动词/カ变动词）
- meaning: 中文释义，有多个常用含义时用分号分隔
- examples: 例句数组，每个例句包含 jp（日文）、html（带注音HTML）、cn（中文翻译）

用户输入的动词：
{words}

请以 JSON 数组格式返回，例如：
```json
[
  {{
    "id": "taberu",
    "word": "食べる",
    "reading": "たべる",
    "display_html": "<ruby>食<rt>た</rt></ruby>べる",
    "type": "一段动词",
    "meaning": "吃",
    "examples": [
      {{
        "jp": "朝ご飯を食べます。",
        "html": "<ruby>朝<rt>あさ</rt></ruby>ご<ruby>飯<rt>はん</rt></ruby>を<ruby>食<rt>た</rt></ruby>べます。",
        "cn": "吃早饭。"
      }}
    ]
  }}
]
```

只返回 JSON，不要有其他说明文字。"""


def get_grammar_prompt(items: str) -> str:
    """获取语法生成提示词"""
    return f"""请将以下日语语法/助词整理为标准格式。每个条目需要包含：
- id: 唯一标识（使用语法的罗马字或缩写）
- title: 语法/助词名称
- reading: 假名读音（如适用）
- display_html: 带注音的 HTML 格式（如适用）
- category: 类别（助词/接续词/句型/敬语/等等）
- meaning: 中文含义和主要用法概述
- usage: 用法说明数组
- examples: 例句数组，每个例句包含 jp（日文）、html（带注音HTML）、cn（中文翻译）

用户输入：
{items}

请以 JSON 数组格式返回，例如：
```json
[
  {{
    "id": "ni_particle",
    "title": "に",
    "reading": "に",
    "display_html": "に",
    "category": "助词",
    "meaning": "表示时间、地点、目的地、对象等",
    "usage": [
      "时间点：三時に起きる（三点起床）",
      "存在地点：東京に住んでいる（住在东京）",
      "移动目的地：学校に行く（去学校）"
    ],
    "examples": [
      {{
        "jp": "七時に起きます。",
        "html": "<ruby>七時<rt>しちじ</rt></ruby>に<ruby>起<rt>お</rt></ruby>きます。",
        "cn": "七点起床。"
      }}
    ]
  }}
]
```

只返回 JSON，不要有其他说明文字。"""


def get_vocabulary_prompt(words: str) -> str:
    """获取词汇生成提示词"""
    return f"""请将以下日语词汇整理为标准格式。每个词汇需要包含：
- id: 唯一标识（使用词汇的罗马字读音）
- word: 词汇
- reading: 假名读音
- display_html: 带注音的 HTML 格式
- type: 词性（名词/形容词/副词/形容动词/连词/感叹词等）
- meaning: 中文释义，有多个常用含义时用分号分隔
- examples: 例句数组，每个例句包含 jp（日文）、html（带注音HTML）、cn（中文翻译）

用户输入：
{words}

请以 JSON 数组格式返回，例如：
```json
[
  {{
    "id": "nihongo",
    "word": "日本語",
    "reading": "にほんご",
    "display_html": "<ruby>日本語<rt>にほんご</rt></ruby>",
    "type": "名词",
    "meaning": "日语",
    "examples": [
      {{
        "jp": "日本語を勉強しています。",
        "html": "<ruby>日本語<rt>にほんご</rt></ruby>を<ruby>勉強<rt>べんきょう</rt></ruby>しています。",
        "cn": "正在学习日语。"
      }}
    ]
  }}
]
```

只返回 JSON，不要有其他说明文字。"""


def get_regenerate_prompt(category: str, item: dict) -> str:
    """获取重新生成单个条目的提示词"""
    if category == "verbs":
        return get_verb_prompt(item.get("word", ""))
    elif category == "grammar":
        return get_grammar_prompt(item.get("title", ""))
    else:
        return get_vocabulary_prompt(item.get("word", ""))


# 提示词映射
PROMPT_GENERATORS = {
    "verbs": get_verb_prompt,
    "grammar": get_grammar_prompt,
    "vocabulary": get_vocabulary_prompt
}


def get_prompt(category: str, content: str) -> str:
    """
    根据类别获取相应的提示词

    Args:
        category: 类别 (verbs/grammar/vocabulary)
        content: 用户输入的内容

    Returns:
        完整的提示词
    """
    generator = PROMPT_GENERATORS.get(category)
    if generator:
        return generator(content)
    else:
        raise ValueError(f"未知的类别: {category}")
