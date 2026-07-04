import html
import os
from typing import Dict, List, Tuple

import gradio as gr
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

APP_THEME = gr.themes.Soft(
    primary_hue="blue",
    secondary_hue="slate",
    neutral_hue="slate",
)

CUSTOM_CSS = """
:root {
  --page-bg: #eef3f8;
  --panel-bg: #ffffff;
  --panel-border: #d8e2ee;
  --soft-text: #667085;
  --main-text: #101828;
  --accent: #2563eb;
  --accent-soft: #eff6ff;
}

body {
  background: linear-gradient(180deg, #f6f8fb 0%, var(--page-bg) 100%);
  font-family: "Segoe UI Variable", "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
}

.gradio-container {
  max-width: none !important;
  margin: 0 !important;
  padding: 0 !important;
}

footer {
  display: none !important;
}

.app-shell {
  gap: 10px;
  align-items: stretch;
  margin: 0 !important;
}

.sidebar-panel,
.chat-panel {
  background: var(--panel-bg);
  border: 1px solid var(--panel-border);
}

.sidebar-panel {
  padding: 8px 8px 10px 10px;
  border-left: none;
  border-top: none;
  border-radius: 0 18px 18px 0;
  box-shadow: none;
  background: #f4f8fc;
}

.chat-panel {
  padding: 6px 14px 10px 14px;
  border-radius: 0 0 0 18px;
  box-shadow: 0 14px 36px rgba(15, 23, 42, 0.06);
  background: #ffffff;
}

.hero {
  margin-bottom: 10px;
}

.hero h1 {
  margin: 0;
  font-size: 1.62rem;
  font-weight: 700;
  color: var(--main-text);
  letter-spacing: -0.02em;
  line-height: 1.12;
}

.hero p {
  margin: 6px 0 0 0;
  color: var(--soft-text);
  font-size: 0.92rem;
  line-height: 1.45;
  max-width: 920px;
}

.sidebar-title {
  display: none !important;
}

.sidebar-title h2 {
  margin: 0;
  font-size: 0.98rem;
  color: var(--main-text);
}

.sidebar-title p {
  margin: 2px 0 0 0;
  color: var(--soft-text);
  font-size: 0.86rem;
  line-height: 1.4;
}

.sidebar-actions {
  gap: 6px;
  margin: 4px 0 6px 0;
}

.sidebar-actions button,
.composer-send button {
  border-radius: 10px !important;
  font-weight: 500 !important;
  min-height: 38px !important;
}

.secondary-btn button {
  background: #f8fafc !important;
  border: 1px solid var(--panel-border) !important;
  color: var(--main-text) !important;
}

.quick-tips {
  margin-top: 8px;
  padding: 8px 10px;
  border-radius: 12px;
  background: #f8fafc;
  border: 1px solid var(--panel-border);
  color: var(--soft-text);
  font-size: 0.79rem;
  line-height: 1.45;
}

.quick-tips strong {
  color: var(--main-text);
}

.chat-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 0px;
  flex-wrap: wrap;
}

.chat-title h1 {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 650;
  color: var(--main-text);
  letter-spacing: -0.01em;
}

.session-chipbar {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.session-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border-radius: 999px;
  background: #f5f8fc;
  border: 1px solid var(--panel-border);
  color: #344054;
  font-size: 0.82rem;
}

#chat-welcome p {
  margin: 0;
}

#main-chatbot {
  border: 1px solid var(--panel-border);
  border-radius: 18px;
  overflow: hidden;
}

#main-chatbot .message {
  max-width: 92% !important;
}

.composer-wrap {
  margin-top: 6px;
  gap: 8px;
  align-items: flex-end;
  padding: 8px;
  border: 1px solid var(--panel-border);
  border-radius: 18px;
  background: #f9fbfd;
}

.composer-wrap textarea,
.composer-wrap input,
.sidebar-panel textarea,
.sidebar-panel input {
  border-radius: 14px !important;
}

.composer-wrap textarea {
  min-height: 92px !important;
}

#small-status {
  min-height: 16px;
  margin: 0px 4px 0px 4px;
  color: var(--soft-text);
  font-size: 0.76rem;
  opacity: 0.72;
}

#small-status p {
  margin: 0;
}

.examples-block {
  margin-top: 4px;
  padding-top: 2px;
}

.examples-block .label-wrap {
  display: none !important;
}

.examples-block button {
  border-radius: 999px !important;
}

.sidebar-panel .gr-accordion {
  margin-top: 6px !important;
}

.sidebar-panel .gr-accordion summary {
  font-weight: 600 !important;
}

.sidebar-panel .wrap,
.chat-panel .wrap {
  box-shadow: none !important;
}

.sidebar-label {
  margin: 6px 0 4px 2px;
  font-size: 0.82rem;
  font-weight: 600;
  color: #475467;
  letter-spacing: 0;
  text-transform: none;
}

.sidebar-panel .gradio-dropdown,
.sidebar-panel .gr-button {
  margin-top: 0 !important;
}

.sidebar-panel .wrap.svelte-1ipelgc,
.sidebar-panel .wrap.svelte-4xt1ch {
  min-height: 42px !important;
}

.sidebar-panel .gr-button button {
  font-size: 0.9rem !important;
  background: #ffffff !important;
  border: 1px solid var(--panel-border) !important;
  color: var(--main-text) !important;
  box-shadow: none !important;
}

.sidebar-panel .gr-accordion summary {
  min-height: 36px !important;
  font-size: 0.9rem !important;
}

.input-hint {
  margin: 2px 4px 0 4px;
  font-size: 0.76rem;
  color: var(--soft-text);
}

"""

# -----------------------------
# Provider config
# -----------------------------
PROVIDERS = {
    "Qwen": {
        "api_key_env": "DASHSCOPE_API_KEY",
        "base_url_env": "QWEN_BASE_URL",
        "default_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "default_model": "qwen-plus",
        "model_options": ["qwen-turbo", "qwen-plus", "qwen-max"],
    },
    "DeepSeek": {
        "api_key_env": "DEEPSEEK_API_KEY",
        "base_url_env": "DEEPSEEK_BASE_URL",
        "default_base_url": "https://api.deepseek.com",
        "default_model": "deepseek-chat",
        "model_options": ["deepseek-chat", "deepseek-reasoner"],
    },
}


def get_default_model_state() -> Dict[str, str]:
    return {
        provider_name: cfg["default_model"] for provider_name, cfg in PROVIDERS.items()
    }


def get_provider_models(provider: str) -> List[str]:
    return PROVIDERS[provider]["model_options"]


def get_client_and_model(provider: str, custom_model: str):
    cfg = PROVIDERS[provider]
    api_key = os.getenv(cfg["api_key_env"], "").strip()
    base_url = os.getenv(cfg["base_url_env"], cfg["default_base_url"]).strip()
    model = custom_model.strip() or cfg["default_model"]

    if not api_key:
        raise ValueError(
            f"Missing API key. Please set environment variable: {cfg['api_key_env']}"
        )

    client = OpenAI(api_key=api_key, base_url=base_url)
    return client, model, base_url


def build_messages(system_prompt: str, history: List[Dict], user_input: str) -> List[Dict]:
    messages: List[Dict] = []
    if system_prompt.strip():
        messages.append({"role": "system", "content": system_prompt.strip()})
    messages.extend(history)
    messages.append({"role": "user", "content": user_input.strip()})
    return messages


def make_status_text(provider: str, model_name: str, error: str = "") -> str:
    if error:
        return f"**Error:** {error}"
    return f"Using **{provider} / {model_name}**"


def get_welcome_messages() -> List[Dict]:
    return [
        {
            "role": "assistant",
            "content": (
                "Welcome. Choose **Qwen** or **DeepSeek** on the left, then start a new conversation here.\n\n"
                "You can ask for reasoning help, math explanations, code snippets, or quick comparisons between models."
            ),
        }
    ]


def render_session_header(provider: str, model_name: str) -> str:
    return (
        '<div class="session-chipbar">'
        f'<div class="session-chip"><strong>Provider</strong> {provider}</div>'
        f'<div class="session-chip"><strong>Model</strong> {model_name}</div>'
        "</div>"
    )


def request_completion(
    provider: str,
    model_name: str,
    system_prompt: str,
    temperature: float,
    top_p: float,
    max_tokens: int,
    history: List[Dict],
    user_input: str,
) -> Tuple[str, str, str]:
    client, resolved_model, _ = get_client_and_model(provider, model_name)
    messages = build_messages(system_prompt, history, user_input)

    response = client.chat.completions.create(
        model=resolved_model,
        messages=messages,
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens,
    )

    assistant_text = response.choices[0].message.content or ""
    status = make_status_text(provider, resolved_model)
    return assistant_text, resolved_model, status


def stream_completion(
    provider: str,
    model_name: str,
    system_prompt: str,
    temperature: float,
    top_p: float,
    max_tokens: int,
    history: List[Dict],
    user_input: str,
):
    client, resolved_model, _ = get_client_and_model(provider, model_name)
    messages = build_messages(system_prompt, history, user_input)
    stream = client.chat.completions.create(
        model=resolved_model,
        messages=messages,
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens,
        stream=True,
    )

    status = make_status_text(provider, resolved_model)
    return stream, resolved_model, status


def format_streaming_text(text: str) -> str:
    escaped = html.escape(text)
    escaped = escaped.replace("\\", "&#92;")
    escaped = escaped.replace("$", "&#36;")
    return escaped


def stream_chat_round(
    provider: str,
    model_name: str,
    system_prompt: str,
    temperature: float,
    top_p: float,
    max_tokens: int,
    prior_history: List[Dict],
    user_input: str,
):
    stream, resolved_model, status = stream_completion(
        provider,
        model_name,
        system_prompt,
        temperature,
        top_p,
        max_tokens,
        prior_history,
        user_input,
    )
    assistant_text = ""
    streaming_history = prior_history + [
        {"role": "user", "content": user_input},
        {"role": "assistant", "content": ""},
    ]

    yield streaming_history, prior_history, status

    for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        if not delta:
            continue

        assistant_text += delta
        streaming_history[-1]["content"] = format_streaming_text(assistant_text)
        yield streaming_history, prior_history, status

    final_history = prior_history + [
        {"role": "user", "content": user_input},
        {"role": "assistant", "content": assistant_text},
    ]
    yield final_history, final_history, make_status_text(provider, resolved_model)


def call_llm(
    provider: str,
    model_name: str,
    system_prompt: str,
    temperature: float,
    top_p: float,
    max_tokens: int,
    user_input: str,
    history_state: List[Dict],
) -> Tuple[List[Dict], List[Dict], str]:
    if not user_input.strip():
        yield history_state, history_state, "**Error:** Please enter a message."
        return

    try:
        yield from stream_chat_round(
            provider,
            model_name,
            system_prompt,
            temperature,
            top_p,
            max_tokens,
            history_state,
            user_input,
        )
    except Exception as e:
        yield history_state, history_state, make_status_text(provider, model_name, str(e))


def regenerate_last_response(
    provider: str,
    model_name: str,
    system_prompt: str,
    temperature: float,
    top_p: float,
    max_tokens: int,
    history_state: List[Dict],
) -> Tuple[List[Dict], List[Dict], str]:
    if len(history_state) < 2:
        yield history_state, history_state, "**Error:** Nothing to regenerate yet."
        return

    last_user = history_state[-2]
    last_assistant = history_state[-1]
    if last_user.get("role") != "user" or last_assistant.get("role") != "assistant":
        yield history_state, history_state, "**Error:** The last round cannot be regenerated."
        return

    prior_history = history_state[:-2]
    user_input = str(last_user.get("content", "")).strip()
    if not user_input:
        yield history_state, history_state, "**Error:** The last user message is empty."
        return

    try:
        yield from stream_chat_round(
            provider,
            model_name,
            system_prompt,
            temperature,
            top_p,
            max_tokens,
            prior_history,
            user_input,
        )
    except Exception as e:
        yield history_state, history_state, make_status_text(provider, model_name, str(e))


def clear_chat():
    return get_welcome_messages(), [], ""


def switch_provider_model(
    new_provider: str,
    current_model: str,
    model_state: Dict[str, str],
    active_provider: str,
):
    new_state = dict(model_state or get_default_model_state())
    previous_provider = active_provider or new_provider

    if previous_provider in PROVIDERS:
        new_state[previous_provider] = current_model or PROVIDERS[previous_provider][
            "default_model"
        ]

    model_options = get_provider_models(new_provider)
    resolved_model = new_state.get(new_provider, PROVIDERS[new_provider]["default_model"])
    if resolved_model not in model_options:
        resolved_model = PROVIDERS[new_provider]["default_model"]

    return (
        gr.update(choices=model_options, value=resolved_model),
        new_state,
        new_provider,
        render_session_header(new_provider, resolved_model),
    )


def update_session_header(provider: str, model_name: str):
    return render_session_header(provider, model_name)


with gr.Blocks(title="Dual-LLM Chat Demo", fill_height=True) as demo:
    with gr.Row(elem_classes="app-shell", equal_height=False):
        with gr.Column(scale=1, min_width=200, elem_classes="sidebar-panel"):
            gr.HTML('<div class="sidebar-label">Provider</div>')
            provider = gr.Dropdown(
                choices=list(PROVIDERS.keys()),
                value="Qwen",
                show_label=False,
            )
            gr.HTML('<div class="sidebar-label">Model</div>')
            model_name = gr.Dropdown(
                choices=get_provider_models("Qwen"),
                value="qwen-plus",
                show_label=False,
            )

            with gr.Row(elem_classes="sidebar-actions"):
                clear_btn = gr.Button("Clear Chat", elem_classes="secondary-btn")
                regenerate_btn = gr.Button("Regenerate")

            with gr.Accordion("Advanced Settings", open=False):
                system_prompt = gr.Textbox(
                    value="You are a helpful assistant. When writing math, use $...$ for inline formulas and $$...$$ for block formulas.",
                    lines=5,
                    label="System Prompt",
                )
                temperature = gr.Slider(
                    0.0, 2.0, value=0.7, step=0.1, label="Temperature"
                )
                top_p = gr.Slider(0.1, 1.0, value=0.9, step=0.1, label="Top-p")
                max_tokens = gr.Slider(
                    2048, 8192, value=4096, step=128, label="Max Tokens"
                )


        with gr.Column(scale=4, min_width=840, elem_classes="chat-panel"):
            with gr.Row(elem_classes="chat-topbar"):
                gr.HTML(
                    """
                    <div class="chat-title">
                      <h1>Dual-LLM Chat</h1>
                    </div>
                    """
                )
                session_header = gr.HTML(render_session_header("Qwen", "qwen-plus"))
            
            chatbot = gr.Chatbot(
                value=get_welcome_messages(),
                height="64vh",
                show_label=False,
                elem_id="main-chatbot",
                autoscroll=True,
                layout="bubble",
                group_consecutive_messages=False,
                buttons=["copy", "copy_all"],
                latex_delimiters=[
                    {"left": "$$", "right": "$$", "display": True},
                    {"left": "$", "right": "$", "display": False},
                    {"left": "\\(", "right": "\\)", "display": False},
                    {"left": "\\[", "right": "\\]", "display": True},
                ],
            )

            with gr.Row(elem_classes="composer-wrap"):
                user_input = gr.Textbox(
                    placeholder="Message Qwen or DeepSeek...",
                    show_label=False,
                    lines=3,
                    max_lines=6,
                    scale=8,
                )
                send_btn = gr.Button("Send", variant="primary", scale=1, elem_classes="composer-send")

            gr.Markdown(
                '<div class="input-hint">Enter for new line, Shift+Enter to send</div>'
            )

            status_md = gr.Markdown("", elem_id="small-status")

    history_state = gr.State([])
    model_state = gr.State(get_default_model_state())
    active_provider_state = gr.State("Qwen")

    provider.change(
        fn=switch_provider_model,
        inputs=[provider, model_name, model_state, active_provider_state],
        outputs=[model_name, model_state, active_provider_state, session_header],
    )

    model_name.change(
        fn=update_session_header,
        inputs=[provider, model_name],
        outputs=session_header,
    )

    send_btn.click(
        fn=call_llm,
        inputs=[
            provider,
            model_name,
            system_prompt,
            temperature,
            top_p,
            max_tokens,
            user_input,
            history_state,
        ],
        outputs=[chatbot, history_state, status_md],
        stream_every=0.25,
    ).then(lambda: "", outputs=user_input)

    user_input.submit(
        fn=call_llm,
        inputs=[
            provider,
            model_name,
            system_prompt,
            temperature,
            top_p,
            max_tokens,
            user_input,
            history_state,
        ],
        outputs=[chatbot, history_state, status_md],
        stream_every=0.25,
    ).then(lambda: "", outputs=user_input)

    clear_btn.click(
        fn=clear_chat,
        outputs=[chatbot, history_state, status_md],
    )

    regenerate_btn.click(
        fn=regenerate_last_response,
        inputs=[
            provider,
            model_name,
            system_prompt,
            temperature,
            top_p,
            max_tokens,
            history_state,
        ],
        outputs=[chatbot, history_state, status_md],
        stream_every=0.25,
    )


if __name__ == "__main__":
    demo.queue().launch(theme=APP_THEME, css=CUSTOM_CSS)
