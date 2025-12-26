"""
日语笔记管理系统 - Streamlit 主应用

功能：
1. 输入词汇/语法，调用 LLM 生成标准格式
2. 审核生成结果，支持重新生成/删除
3. 管理已有条目（查看/删除）
4. 配置 API 设置
5. 构建并部署网站
"""

import streamlit as st
import time
import subprocess
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.llm_client import LLMClient
from app.data_manager import (
    load_data, save_data, add_items, delete_items, update_item,
    get_statistics, generate_id
)
from app.config import (
    load_api_configs, save_api_configs,
    CATEGORIES, PROJECT_ROOT
)
from app.prompts import get_prompt, SYSTEM_PROMPT


# ============== 页面配置 ==============
st.set_page_config(
    page_title="日语笔记",
    page_icon="🇯🇵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义 CSS
st.markdown("""
<style>
    /* Ruby 注音样式 */
    ruby {
        ruby-position: over;
    }
    rt {
        font-size: 0.6em;
        color: #666;
    }

    /* 卡片样式 */
    .vocab-card {
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #ddd;
        margin-bottom: 1rem;
        background: white;
    }

    .vocab-word {
        font-size: 1.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }

    /* 例句样式 */
    .example-box {
        background: #f8f9fa;
        padding: 0.8rem;
        border-left: 3px solid #4CAF50;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


# ============== Session State 初始化 ==============
def init_session_state():
    """初始化 session state"""
    if "api_configs" not in st.session_state:
        st.session_state.api_configs = load_api_configs()

    if "staged_items" not in st.session_state:
        st.session_state.staged_items = {}    # {category: [items]}

init_session_state()


# ============== LLM 客户端 ==============
def get_llm_client():
    """获取 LLM 客户端实例"""
    return LLMClient(st.session_state.api_configs)


# ============== 侧边栏 ==============
def render_sidebar():
    """渲染侧边栏"""
    with st.sidebar:
        st.title("🇯🇵 日语笔记")

        # 统计信息
        stats = get_statistics()
        st.markdown("### 📊 统计")
        cols = st.columns(3)
        for i, (cat, info) in enumerate(CATEGORIES.items()):
            cols[i].metric(info["icon"] + " " + info["name"], stats.get(cat, 0))

        st.divider()

        # 模式选择
        mode = st.radio(
            "选择模式",
            ["➕ 添加词汇", "📋 管理词汇", "⚙️ 设置"],
            label_visibility="collapsed"
        )

        st.divider()

        # API 状态
        with st.expander("🔌 API 状态", expanded=False):
            config_names = set()
            for config in st.session_state.api_configs:
                status = "✅" if config.get("key") else "⚪"
                if config["name"] not in config_names:
                    config_names.add(config["name"])
                    st.text(f"{status} {config['name']}")

        # 构建按钮
        st.divider()
        if st.button("🚀 构建网站", use_container_width=True):
            build_website()

        return mode


# ============== 添加词汇模式 ==============
def render_add_mode():
    """渲染添加词汇模式"""
    st.header("➕ 添加新词汇")

    # 创建 tabs
    tabs = st.tabs([f"{info['icon']} {info['name']}" for info in CATEGORIES.values()])

    for i, (category, info) in enumerate(CATEGORIES.items()):
        with tabs[i]:
            render_input_section(category, info)


def render_input_section(category: str, info: dict):
    """渲染输入区域"""
    st.markdown(f"**{info['description']}**")

    PLACEHOLDERS = {
        "verbs": "例如：\n食べる\nお腹が空いて 这句话里的动词",
        "grammar": "例如：\n〜ている\n荷物が重くて持てません 这句话第一个 te 的用法",
        "vocabulary": "例如：\n猫\nおもい（是重的意思，不是思那个）"
    }

    # 输入框
    input_key = f"input_{category}"
    clear_flag = f"clear_input_{category}"
    if st.session_state.get(clear_flag, False):
        st.session_state[input_key] = ""
        st.session_state[clear_flag] = False
    user_input = st.text_area(
        f"输入{info['name']}（每行一个）",
        height=150,
        key=input_key,
        placeholder=PLACEHOLDERS.get(category, "")
    )

    col1, col2 = st.columns([1, 4])
    with col1:
        generate_btn = st.button(
            "🔮 生成",
            key=f"gen_{category}",
            use_container_width=True,
            disabled=not user_input.strip()
        )

    # 生成处理
    if generate_btn and user_input.strip():
        with st.spinner("正在调用 LLM 生成内容..."):
            generate_content(category, user_input.strip())

    # 显示暂存区
    render_staging_area(category)


def generate_content(category: str, content: str):
    """调用 LLM 生成内容"""
    client = get_llm_client()
    prompt = get_prompt(category, content)

    try:
        response = client.call(prompt, SYSTEM_PROMPT)

        if response:
            # 解析 JSON
            parsed = client.parse_json_response(response)

            if parsed and isinstance(parsed, list):
                # 为每个条目添加时间戳和唯一 ID
                for item in parsed:
                    if "created_at" not in item:
                        item["created_at"] = int(time.time())
                    if not item.get("id"):
                        word = item.get("reading") or item.get("word") or item.get("title", "")
                        item["id"] = generate_id(word)
                    else:
                        item["id"] = generate_id(item["id"], convert=False)

                # 保存到暂存区
                if category not in st.session_state.staged_items:
                    st.session_state.staged_items[category] = []
                st.session_state.staged_items[category].extend(parsed)

                st.success(f"成功生成 {len(parsed)} 个条目 (使用 {client.last_used_api})")
            else:
                st.error("无法解析 LLM 响应，请重试")
                if response:
                    with st.expander("查看原始响应"):
                        st.code(response)
        else:
            st.error(f"LLM 调用失败: {client.last_error}")
    except Exception as e:
        st.error(f"生成出错: {str(e)}")


def render_staging_area(category: str):
    """渲染暂存区（审核区）"""
    items = st.session_state.staged_items.get(category, [])

    if not items:
        return

    st.divider()
    st.subheader("📝 待确认的条目")

    # 创建选择状态
    if f"selected_{category}" not in st.session_state:
        st.session_state[f"selected_{category}"] = {}

    # 显示每个条目
    for idx, item in enumerate(items):
        with st.container():
            col1, col2, col3 = st.columns([0.5, 8, 1.5])

            with col1:
                # 删除选择框
                delete_key = f"del_{category}_{idx}"
                st.checkbox("🗑️", key=delete_key, label_visibility="collapsed")

            with col2:
                # 显示条目内容
                display = item.get("display_html") or item.get("word") or item.get("title", "")
                meaning = item.get("meaning", "")
                item_type = item.get("type") or item.get("category", "")

                st.markdown(f"<div>                                             \
                                <strong>{display}</strong>                      \
                                <span style='color:#666'>（{item_type}）</span>  \
                            </div>", unsafe_allow_html=True)
                st.markdown(f"*{meaning}*")

                # 显示例句
                examples = item.get("examples", [])
                usage = item.get("usage", [])
                if examples or usage:
                    with st.expander("查看例句"):
                        if usage:
                            st.markdown("**用法**:")
                            for u in usage:
                                st.markdown(f"- {u}")
                        if examples:
                            st.markdown("**例句**:")
                            for ex in examples:
                                st.markdown(f"""
                                <div class="example-box">
                                    {ex.get('html', ex.get('jp', ''))}
                                    <br><small>{ex.get('cn', '')}</small>
                                </div>
                                """, unsafe_allow_html=True)

            with col3:
                # 重新生成按钮
                if st.button("🔄", key=f"regen_{category}_{idx}", help="重新生成"):
                    regenerate_item(category, idx, item)

        st.divider()

    # 操作按钮
    col1, col2, col3, col4 = st.columns([1, 1, 1, 2])

    with col1:
        if st.button("✅ 确认入库", key=f"confirm_{category}", type="primary"):
            confirm_items(category)

    with col2:
        if st.button("🗑️ 删除选中", key=f"delete_selected_{category}"):
            delete_selected_items(category)

    with col3:
        if st.button("❌ 清空全部", key=f"clear_{category}"):
            st.session_state.staged_items[category] = []
            st.rerun()


def regenerate_item(category: str, idx: int, item: dict):
    """重新生成单个条目"""
    client = get_llm_client()
    word = item.get("word") or item.get("title")
    if not word:
        st.error("无法重新生成：缺少关键词")
        return
    prompt = get_prompt(category, word)

    with st.spinner(f"正在重新生成 '{word}'..."):
        response = client.call(prompt, SYSTEM_PROMPT)

        if response:
            parsed = client.parse_json_response(response)
            if parsed and isinstance(parsed, list) and len(parsed) > 0:
                new_item = parsed[0]
                new_item["created_at"] = item.get("created_at", int(time.time()))
                if not new_item.get("id"):
                    new_item["id"] = generate_id(item.get("reading", word))
                else:
                    new_item["id"] = generate_id(new_item["id"], convert=False)
                st.session_state.staged_items[category][idx] = new_item
                st.success("重新生成成功")
                st.rerun()


def delete_selected_items(category: str):
    """删除选中的条目"""
    items = st.session_state.staged_items.get(category, [])
    new_items = []

    for idx, item in enumerate(items):
        delete_key = f"del_{category}_{idx}"
        if not st.session_state.get(delete_key, False):
            new_items.append(item)

    st.session_state.staged_items[category] = new_items
    st.rerun()


def confirm_items(category: str):
    """确认入库"""
    items = st.session_state.staged_items.get(category, [])

    if not items:
        st.warning("没有待确认的条目")
        return

    result = add_items(category, items)
    st.success(f"入库完成: 新增 {result['added']} 条记录")

    # 清空暂存区与输入区
    st.session_state.staged_items[category] = []
    clear_flag = f"clear_input_{category}"
    st.session_state[clear_flag] = True

    st.rerun()


# ============== 管理词汇模式 ==============
def render_manage_mode():
    """渲染管理词汇模式"""
    st.header("📋 管理词汇")

    tabs = st.tabs([f"{info['icon']} {info['name']}" for info in CATEGORIES.values()])

    for i, (category, info) in enumerate(CATEGORIES.items()):
        with tabs[i]:
            render_manage_section(category, info)


def render_manage_section(category: str, info: dict):
    """渲染管理区域"""
    data = load_data(category)

    if not data:
        st.info(f"暂无{info['name']}数据")
        return

    st.markdown(f"共 **{len(data)}** 条记录")

    # 搜索框
    search = st.text_input("🔍 搜索", key=f"search_{category}", placeholder="输入关键词...")

    if search:
        data = [item for item in data if
                search.lower() in str(item.get("word", "")).lower() or
                search.lower() in str(item.get("title", "")).lower() or
                search.lower() in str(item.get("meaning", "")).lower() or
                search.lower() in str(item.get("reading", "")).lower()]

    # 显示数据
    selected_ids = []

    for idx, item in enumerate(data):
        with st.container():
            col1, col2 = st.columns([0.5, 9.5])

            with col1:
                if st.checkbox("删除", key=f"manage_sel_{category}_{idx}", label_visibility="collapsed"):
                    selected_ids.append(item.get("id"))

            with col2:
                display = item.get("word") or item.get("title") or item.get("reading", "")
                meaning = item.get("meaning", "")
                item_type = item.get("type") or item.get("category", "")

                # 使用 expander 显示详情
                with st.expander(f"**{display}** - {meaning}"):
                    st.markdown(f"**类型**：{item_type}")
                    st.markdown(f"**读音**：{item.get('reading', '')}")

                    usage = item.get("usage", [])
                    if usage:
                        st.markdown("**用法**：")
                        for u in usage:
                            st.markdown(f"- {u}")

                    examples = item.get("examples", [])
                    if examples:
                        st.markdown("**例句**：")
                        for ex in examples:
                            st.markdown(f"""
                                <div class="example-box">
                                    {ex.get('html', ex.get('jp', ''))}
                                    <br><small>{ex.get('cn', '')}</small>
                                </div>
                                """, unsafe_allow_html=True
                            )

                    if item.get("notes"):
                        st.markdown(f"**备注**：")
                        st.markdown(f"""
                            <div class="example-box">
                                {item.get('notes', '').replace('\n', '<br>')}
                            </div>
                            """, unsafe_allow_html=True
                        )

                    # 备注输入与保存
                    note_key = f"note_input_{category}_{item.get('id')}"
                    current_note = item.get("notes", "")
                    note_val = st.text_area("编辑备注", value=current_note, key=note_key, height=80,
                                            placeholder="添加备注，留空保存则删除备注")
                    if st.button("💾 保存备注", key=f"save_note_{category}_{item.get('id')}"):
                        success = update_item(category, item.get("id"), {"notes": note_val})
                        if success:
                            st.success("备注已保存") # 实际上看不到这个，因为会刷新
                            st.rerun()
                        else:
                            st.error("保存备注失败")

    # 删除按钮
    if st.button(f"🗑️ 删除选中 ({len(selected_ids)} 条)", key=f"del_manage_{category}",
                 disabled=len(selected_ids) == 0):
        if selected_ids:
            deleted = delete_items(category, selected_ids)
            st.success(f"已删除 {deleted} 条记录")
            st.rerun()


# ============== 设置模式 ==============
def render_settings_mode():
    """渲染设置模式"""
    st.header("⚙️ 设置")

    tab1, = st.tabs(["🔌 API 配置"])

    with tab1:
        render_api_settings()


def render_api_settings():
    """渲染 API 设置"""
    st.subheader("API 优先级设置")
    st.markdown("调整 API 优先级，系统会按顺序尝试调用")

    configs = st.session_state.api_configs

    if "selected_api_index" not in st.session_state:
        st.session_state.selected_api_index = None

    # 调整优先级
    col1, col2, col3, col4 = st.columns([3, 1, 1, 6])

    with col1:
        if configs:
            options = [f"{cfg['name']} - {cfg['model']}" for i, cfg in enumerate(configs)]
            default_idx = st.session_state.selected_api_index if st.session_state.selected_api_index is not None else 0
            selected_label = st.radio("当前选中 API", options=options, index=default_idx, key="api_selected", label_visibility="collapsed")
            st.session_state.selected_api_index = options.index(selected_label)

    selected_idx = st.session_state.selected_api_index

    with col2:
        if st.button(
            "⬆️ 上移",
            key="move_up",
            disabled=(selected_idx is None or selected_idx == 0)
        ):
            if selected_idx is not None and selected_idx > 0:
                configs[selected_idx], configs[selected_idx - 1] = \
                    configs[selected_idx - 1], configs[selected_idx]
                st.session_state.selected_api_index = selected_idx - 1
                st.rerun()

    with col3:
        if st.button(
            "⬇️ 下移",
            key="move_down",
            disabled=(selected_idx is None or selected_idx == len(configs) - 1)
        ):
            if selected_idx is not None and selected_idx < len(configs) - 1:
                configs[selected_idx], configs[selected_idx + 1] = \
                    configs[selected_idx + 1], configs[selected_idx]
                st.session_state.selected_api_index = selected_idx + 1
                st.rerun()

    for i, config in enumerate(configs):
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([0.5, 2, 2, 1, 1])

            with col1:
                st.markdown(f"**{i+1}.**")

            with col2:
                st.markdown(f"**{config['name']}** - {config['model']}")

            with col3:
                st.markdown(f"`{config['type']}`")

            with col4:
                has_key = bool(config.get("key"))
                st.markdown("🔑 已配置" if has_key else "⚠️ 未配置")

            with col5:
                safe_name = str(config.get("name", "")).replace(" ", "_") \
                    + "_" + str(config.get("model", "")).replace(" ", "_")
                key_enabled = f"api_enabled_{safe_name}"
                st.session_state.setdefault(key_enabled, config.get("enabled", False))
                st.checkbox("启用", key=key_enabled)
                config["enabled"] = st.session_state[key_enabled] # 同步状态

        st.divider()

    # 保存配置
    if st.button("💾 保存配置", type="primary"):
        save_api_configs(configs)
        st.success("配置已保存")
        st.session_state.selected_api_index = None

    st.divider()
    st.subheader("API Key 配置")
    st.info("""
    API Key 应保存在 `.streamlit/secrets.toml` 文件中,例如:
    ```toml
    DEEPSEEK_API_KEY = "your-key"
    OPENAI_API_KEY = "your-key"
    GOOGLE_API_KEY = "your-key"
    ```
    """)


# ============== 构建网站 ==============
def build_website():
    """构建静态网站"""
    with st.spinner("正在构建网站..."):
        try:
            # 运行 build.py
            result = subprocess.run(
                [sys.executable, str(PROJECT_ROOT / "build.py")],
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                st.error(f"构建失败: {result.stderr}")
                return

            st.success("网站构建成功！")
            st.info("运行 `mkdocs serve` 可本地预览")

            # git push
            git_add_result = subprocess.run(
                ["git", "add", "."],
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                text=True
            )
            if git_add_result.returncode != 0:
                st.error(f"git add 失败: {git_add_result.stderr}")
                return

            commit_cmd = [
                "git",
                "-c", "user.name=auto-bot",
                "-c", "user.email=auto-bot@example.com",
                "commit",
                "-m", "chore: update site content"
            ]
            git_commit_result = subprocess.run(
                commit_cmd,
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                text=True
            )
            if git_commit_result.returncode != 0:
                if "nothing to commit" in git_commit_result.stderr:
                    st.info("没有新的更改需要提交！")
                else:
                    st.error(f"git commit 失败: {git_commit_result.stderr}")
                    return

            git_push_result = subprocess.run(
                ["git", "push"],
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                text=True
            )
            if git_push_result.returncode != 0:
                st.error(f"git push 失败: {git_push_result.stderr}")
                return

            st.success("网站已推送到远程仓库！")

        except Exception as e:
            st.error(f"构建出错: {str(e)}")


# ============== 主程序 ==============
def main():
    """主函数"""
    mode = render_sidebar()

    if "添加" in mode:
        render_add_mode()
    elif "管理" in mode:
        render_manage_mode()
    else:
        render_settings_mode()


if __name__ == "__main__":
    main()
