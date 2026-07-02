# ⚡ Right Click AI

> Asisten AI yang terintegrasi langsung ke workflow Windows kamu. Sorot teks, tekan hotkey, dan dapatkan jawaban instan.

![Platform](https://img.shields.io/badge/Platform-Windows-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Version](https://img.shields.io/badge/Version-0.1.0-purple)

## ✨ Fitur

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

## 🧠 AI Provider

| Provider | Tipe | Vision |
|---|---|---|
| Ollama | Local (Gratis) | ✅ |
| OpenAI | Cloud (BYOK) | ✅ |
| Google Gemini | Cloud (BYOK) | ✅ |
| Anthropic | Cloud (BYOK) | ✅ |
| OpenRouter | Cloud (BYOK) | ✅ |

## 🚀 Quick Start

### Prasyarat

- **Python 3.10+** — [Download](https://python.org)
- **Node.js 18+** — [Download](https://nodejs.org)
- **Ollama** (opsional, untuk local AI) — [Download](https://ollama.ai)

### Instalasi

```bash
# Clone repository
git clone https://github.com/your-username/rightclick-ai.git
cd rightclick-ai

# Jalankan (auto-setup pada pertama kali)
start.bat
```

Script `start.bat` akan secara otomatis:
1. Membuat Python virtual environment
2. Menginstall semua dependencies
3. Menjalankan backend API server
4. Membuka aplikasi Electron

### Penggunaan

1. **Sorot teks** di aplikasi mana pun (browser, Notepad, Word, dll)
2. **Copy** teks yang disorot (`Ctrl+C`)
3. **Tekan** `Ctrl+Shift+Q`
4. **Pilih aksi** dari menu popup yang muncul
5. **Lihat hasilnya** di widget mengambang

## 📦 Tech Stack

- **Frontend:** Electron + Vanilla JS/CSS
- **Backend:** Python + FastAPI
- **AI:** Ollama (local), OpenAI, Gemini, Anthropic, OpenRouter (BYOK)

## 📄 Lisensi

MIT License
