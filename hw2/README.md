# Lab 2 - LLM Application

## 1. Project Overview

This project is a visual LLM chat application built with **Gradio** and **OpenAI-compatible APIs**.

It supports models from **two different companies**:
- Qwen (Alibaba)
- DeepSeek

So it satisfies the assignment requirement of calling at least two different companies' LLM APIs.


## 2. Environment Requirements

- Python 3.10 or newer
- Internet access for model APIs

Install dependencies:

```powershell
pip install gradio openai python-dotenv
```

## 3. Environment Variables (`.env`)

Create a `.env` file in the project root:

```env
# Qwen
DASHSCOPE_API_KEY=your_qwen_api_key
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# DeepSeek
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

Notes:
- Base URLs can be omitted if default URLs are used.
- At least one valid API key is required to chat.

## 4. How to Run

From the project directory:

```powershell
python app.py
```

Then open the local URL shown in terminal (usually `http://127.0.0.1:7860`).

## 5. How to Use

1. Select `Provider` (`Qwen` or `DeepSeek`).
2. Select `Model`.
3. (Optional) adjust `System Prompt`, `Temperature`, `Top-p`, `Max Tokens`.
4. Type a message and click `Send`.
5. Use `Regenerate` to regenerate the last assistant answer.
6. Use `Clear Chat` to clear current session.

## 6. Main Features in Current App

- Multi-provider API switching
- Multi-turn context in current session
- Streaming output (for better perceived responsiveness)
- Regenerate last response
- Adjustable generation parameters
- Polished custom Gradio UI

## 7. Troubleshooting

### `Missing API key`
Check `.env` variable names and values:
- `DASHSCOPE_API_KEY`
- `DEEPSEEK_API_KEY`

### Response is slow
- Lower `Max Tokens`
- Choose a faster model
- Clear long conversation history

### Output seems truncated
- Increase `Max Tokens`
- Shorten input or reduce context length


