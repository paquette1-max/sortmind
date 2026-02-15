# 🧠 SortMind

> **AI-powered document organization. 100% local. Privacy-first.**

SortMind intelligently analyzes your documents and suggests descriptive filenames and organized folder structures—all running locally on your machine with Ollama. No cloud. No data leaving your computer.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey.svg)

## ✨ Features

### Free Tier
- 📁 **Smart Organization** - Pattern-based file sorting
- 🔍 **Duplicate Detection** - Find and remove duplicate files
- ⚡ **Fast Processing** - Local analysis, no internet required
- 🎯 **Manual Review** - Approve suggestions before applying
- 🧪 **5 Free AI Analyses** - Try intelligent document analysis

### Pro Tier ($49 one-time)
- 🧠 **AI Document Analysis** - Understands content, suggests intelligent names
- 📄 **Multi-format Support** - PDF, images, Office docs, text files
- 🔄 **Batch Processing** - Organize hundreds of files at once
- 🎨 **Custom Patterns** - Create your own organization rules
- 🔒 **100% Local** - All AI runs via Ollama, zero cloud dependency

### Enterprise Tier ($199 one-time)
- ☁️ **Cloud Sync** - Optional encrypted backup to S3/Dropbox
- 🎧 **Priority Support** - Direct email support
- 🏢 **Team Features** - Multi-user deployment options

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/ash-works/sortmind.git
cd sortmind

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install OCR dependencies (macOS)
brew install tesseract poppler

# Install and start Ollama
brew install ollama
ollama serve

# Pull the AI model
ollama pull llama3.2:3b

# Launch SortMind
python src/main.py
```

### First Run

1. **Select a folder** - Choose documents to organize
2. **Try AI analysis** (5 free uses) - Let SortMind understand your files
3. **Review suggestions** - Approve suggested names and locations
4. **Apply organization** - One-click to reorganize

## 🎨 The SortMind Approach

### Three-Pass Intelligence

1. **Pattern Pass** - Regex-based extraction (fast, high confidence)
2. **AI Pass** - Local LLM analysis (medium confidence)
3. **Review Pass** - Your final approval (complete control)

### Example

```
scan_001.pdf
    ↓ SortMind AI Analysis
Chase_Bank_Statement_2025-05.pdf
    ↓ Suggested Location
~/Documents/Finance/Banks/Chase/2025/
```

## 🔐 Privacy-First Architecture

- **No cloud APIs** - All processing via local Ollama
- **No data collection** - Zero telemetry
- **No internet required** - Works offline
- **Open source** - Audit the code yourself

## 💰 Licensing

SortMind uses an **open-core model**:

- **Free**: Pattern-based organization, manual review
- **Pro ($49)**: AI analysis, batch processing, custom patterns
- **Enterprise ($199)**: Cloud sync, priority support

[Upgrade via GitHub Sponsors](https://github.com/sponsors/ash-works)

## 🛠️ Tech Stack

- **Python 3.8+** - Core application
- **PyQt6** - Cross-platform GUI
- **Ollama** - Local LLM inference
- **PyMuPDF + pdfplumber** - PDF extraction
- **Tesseract** - OCR for scanned documents
- **SQLite** - Local data storage

## 📖 Documentation

- [User Guide](USER_GUIDE.md) - Complete usage instructions
- [Market Analysis](MARKET_ANALYSIS.md) - Business strategy & positioning
- [Local LLM Setup](LOCAL_LLM_SETUP.md) - Configure Ollama

## 🤝 Contributing

Contributions welcome! Please read our [Contributing Guide](CONTRIBUTING.md) first.

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with ❤️ by [ash-works](https://github.com/ash-works)
- Inspired by [Hazel](https://www.noodlesoft.com/) (Mac) and [Paperless-ngx](https://docs.paperless-ngx.com/)
- AI powered by [Ollama](https://ollama.com/)

---

<p align="center">
  <b>SortMind</b> — Documents, intelligently organized.
</p>
