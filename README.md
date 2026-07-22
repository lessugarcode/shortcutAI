# ⚡ Right Click AI

> Asisten AI yang terintegrasi langsung ke workflow Windows kamu. Sorot teks, tekan hotkey, dan dapatkan jawaban instan.

![Platform](https://img.shields.io/badge/Platform-Windows-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Version](https://img.shields.io/badge/Version-0.2.0-amber)

## ✨ Fitur

### 🤖 Aksi AI
- 🌐 **Terjemahkan** — Terjemahkan teks ke 14+ bahasa
- 📖 **Jelaskan** — Penjelasan sederhana seperti ELI5
- 📝 **Ringkas** — Buat ringkasan instan
- ✍️ **Perbaiki Tulisan** — Grammar check otomatis
- 🐛 **Jelaskan Kode** — Pahami kode dalam hitungan detik
- 🔍 **Review Kode** — Temukan bug dan saran perbaikan
- 🖼️ **Jelaskan Gambar** — Vision AI untuk gambar
- 📄 **OCR** — Ekstrak teks dari gambar
- 💬 **Tanya AI** — Free-form prompt untuk segala hal
- ⚙️ **Custom Prompts** — Buat aksi AI kustom sendiri

### 🎨 UX
- ⌨️ **Keyboard Shortcuts** — Tekan `1-9` untuk pilih aksi, `/` untuk fokus input
- 📋 **Auto-paste** — Otomatis paste hasil AI kembali ke aplikasi sumber
- 📜 **History** — Semua interaksi AI tersimpan dan bisa dicari ulang
- 📥 **Export** — Download history sebagai file Markdown
- 📌 **Pin Window** — Kunci widget hasil agar tetap di atas
- ⚡ **Streaming** — Lihat jawaban AI muncul kata per kata

### 🔐 Keamanan
- 🔒 **Auth Token** — Komunikasi backend ↔ frontend diamankan dengan shared secret
- 🛡️ **Windows Credential Manager** — API key disimpan di OS-native secure storage
- 🚦 **Rate Limiting** — 30 request/menit per IP
- 🔑 **Enkripsi** — Fallback ke Fernet encryption bila keyring tidak tersedia

## 🧠 AI Provider

| Provider | Tipe | Vision | Retry Logic |
|---|---|---|---|
| Ollama | Local (Gratis) | ✅ | ✅ |
| OpenAI | Cloud (BYOK) | ✅ | — |
| Google Gemini | Cloud (BYOK) | ✅ | ✅ |
| Anthropic | Cloud (BYOK) | ✅ | — |
| OpenRouter | Cloud (BYOK) | ✅ | — Quick Start

### Prasyarat

- **Python 3.10+** — [Download](https://python.org)
- **Node.js 18+** — [Download](https://nodejs.org)
- **Ollama** (opsional, untuk local AI) — [Download](https://ollama.ai)

### Instalasi

```bash
git clone https://github.com/lessugarcode/shortcutAI.git
cd shortcutAI
start.bat
```

`start.bat` akan otomatis:
1. Membuat Python virtual environment
2. Menginstall semua dependencies
3. Menjalankan backend API server
4. Membuka aplikasi Electron

### Penggunaan

1. **Sorot teks** di aplikasi mana pun (browser, Notepad, Word, dll)
2. **Copy** teks yang disorot (`Ctrl+C`)
3. **Tekan** `Ctrl+Shift+Q` (bisa dikustomisasi di Settings)
4. **Pilih aksi** dari menu popup (klik atau tekan `1-9`)
5. **Lihat hasilnya** di widget mengambang
6. **Copy/Paste** hasil atau biarkan Auto-paste mengembalikannya

### Konfigurasi API Key

Buka **Settings** (klik kanan tray icon → ⚙️ Settings, atau window muncul di first launch).
Isi API key di tab **Providers** untuk provider yang ingin dipakai.

API key disimpan aman menggunakan **Windows Credential Manager** (atau fallback ke Fernet encryption bila keyring tidak tersedia).

## 📦 Tech Stack

- **Frontend:** Electron + Vanilla JS/CSS (Luxury Dark theme)
- **Backend:** Python 3.12 + FastAPI + Uvicorn
- **AI:** Ollama (local), OpenAI, Gemini, Anthropic, OpenRouter (BYOK)
- **Storage:** SQLite (history), Windows Credential Manager (API keys)
- **Security:** Auth token middleware, Rate limiting, Keyring encryption

## 📂 Struktur Proyek

```
rightclickAI/
├── backend/               # Python FastAPI server/         # AI provider implementations
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

## 📄 Lisensi

MIT License
