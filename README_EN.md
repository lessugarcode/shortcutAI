# ⚡ Right Click AI

> AI assistant integrated directly into your Windows workflow. Highlight text, press a hotkey, get instant answers.

![Platform](https://img.shields.io/badge/Platform-Windows-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Version](https://img.shields.io/badge/Version-0.2.0-amber)

## ✨ Features

### 🤖 AI Actions
- 🌐 **Translate** — Translate text to 14+ languages
- 📖 **Explain** — Simple ELI5-style explanations
- 📝 **Summarize** — Generate instant summaries
- ✍️ **Fix Writing** — Automatic grammar check & proofread
- 🐛 **Explain Code** — Understand code in seconds
- 🔍 **Review Code** — Find bugs and improvement suggestions
- 🖼️ **Describe Image** — Vision AI for images
- 📄 **OCR** — Extract text from images
- 💬 **Ask AI** — Free-form prompts for anything
- ⚙️ **Custom Prompts** — Create your own AI actions

### 🎨 UX
- ⌨️ **Keyboard Shortcuts** — Press `1-9` to select actions, `/` to focus input
- 📋 **Auto-paste** — Automatically paste AI results back to source app
- 📜 **History** — All AI interactions saved and searchable
- 📥 **Export** — Download history as a Markdown file
- 📌 **Pin Window** — Keep result widget always on top
- ⚡ **Streaming** — Watch AI responses appear word by word

### 🔐 Security
- 🔒 **Auth Token** — Backend ↔ frontend communication secured with shared secret
- 🛡️ **Windows Credential Manager** — API keys stored in OS-native secure storage
- 🚦 **Rate Limiting** — 30 requests/minute per IP
- 🔑 **Encryption** — Fernet encryption fallback when keyring is unavailable

## 🧠 AI Providers

| Provider | Type | Vision | Retry Logic |
|---|---|---|---|
| Ollama | Local (Free) | ✅ | ✅ |
| OpenAI | Cloud (BYOK) | ✅ | — |
| Google Gemini | Cloud (BYOK) | ✅ | ✅ |
| Anthropic | Cloud (BYOK) | ✅ | — |
| OpenRouter | Cloud (BYOK) | ✅ | — |

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+** — [Download](https://python.org)
- **Node.js 18+** — [Download](https://nodejs.org)
- **Ollama** (optional, for local AI) — [Download](https://ollama.ai)

### Installation

```bash
git clone https://github.com/lessugarcode/shortcutAI.git
cd shortcutAI
start.bat
```

`start.bat` automatically:
1. Creates a Python virtual environment
2. Installs all dependencies
3. Starts the backend API server
4. Launches the Electron app

### Usage

1. **Highlight text** in any app (browser, Notepad, Word, etc.)
2. **Copy** highlighted text (`Ctrl+C`)
3. **Press** `Ctrl+Shift+Q` (customizable in Settings)
4. **Select an action** from the popup menu (click or press `1-9`)
5. **View results** in the floating widget
6. **Copy/Paste** results or let Auto-paste send it back

### API Key Configuration

Open **Settings** (right-click tray icon → ⚙️ Settings, or the window appears on first launch).
Enter your API key in the **Providers** tab for your preferred provider.

API keys are stored securely using **Windows Credential Manager** (with Fernet encryption fallback when keyring is unavailable).

## 📦 Tech Stack

- **Frontend:** Electron + Vanilla JS/CSS (Luxury Dark theme)
- **Backend:** Python 3.12 + FastAPI + Uvicorn
- **AI:** Ollama (local), OpenAI, Gemini, Anthropic, OpenRouter (BYOK)
- **Storage:** SQLite (history), Windows Credential Manager (API keys)
- **Security:** Auth token middleware, Rate limiting, Keyring encryption

## 📂 Project Structure

```
rightclickAI/
├── backend/               # Python FastAPI server
│   ├── providers/         # AI provider implementations
│   ├── routers/           # API endpoints (ai, settings)
│   ├── services/          # Business logic (actions, history, rate_limiter, context)
│   ├── tests/             # Unit & integration tests
│   ├── utils/             # Security, encryption
│   ├── config.py          # Configuration management
│   └── main.py            # FastAPI entry point
├── electron/              # Electron desktop app
│   ├── src/
│   │   ├── js/            # Frontend logic (api, popup, result, settings)
│   │   ├── pages/         # HTML pages (popup, result, └── styles/        # CSS design system
│   ├── main.js            # Electron main process
│   └── preload.js         # Context bridge
└── start.bat              # One-click launcher
```

## 📄 License

MIT License
