# AI File Organizer - User Guide

**Version:** 1.0  
**Last Updated:** January 2026  
**Application Status:** Production Ready (Phases 1-4 Complete)

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [System Requirements](#system-requirements)
3. [Installation Guide](#installation-guide)
4. [Local LLM Setup](#local-llm-setup)
5. [Application Configuration](#application-configuration)
6. [Using the Application](#using-the-application)
7. [Troubleshooting](#troubleshooting)
8. [Tips & Best Practices](#tips--best-practices)
9. [Suggested Enhancements](#suggested-enhancements)

---

## Getting Started

AI File Organizer is a desktop application that uses artificial intelligence to automatically organize your files. It analyzes file content and suggests logical categories and names—all while keeping your data completely private by running locally on your computer.

### What You'll Need:
- A computer (Windows, macOS, or Linux)
- 8GB+ RAM recommended
- A local LLM (we'll show you how to install one)
- About 30 minutes for initial setup

### What This App Does:
- 📁 **Analyzes files** - Reads content to understand what each file contains
- 🏷️ **Suggests categories** - Organizes files into logical folders
- ✏️ **Renames intelligently** - Creates meaningful file names
- 🔒 **Keeps data private** - Everything runs locally on your computer
- ↩️ **Can undo changes** - Made a mistake? Easily revert operations
- 💾 **Creates backups** - Automatically backs up files before changes

---

## System Requirements

### Minimum Requirements:
- **CPU:** Intel Core i5 / AMD Ryzen 5 or Apple Silicon M1 and newer
- **RAM:** 8GB (16GB+ recommended)
- **Disk Space:** 5GB for application and local LLM
- **OS:** Windows 10+, macOS 10.15+, or Linux (Ubuntu 20.04+)

### Recommended Setup:
- **CPU:** Apple Silicon (M1/M2/M3/M4) or Modern Intel/AMD processor
- **RAM:** 16GB or more
- **Disk Space:** 10GB+ (allows for larger LLM models)
- **SSD:** For faster file processing

### Network:
- Optional internet connection (only for setup and updates)
- No internet required during actual use (fully local operation)

---

## Installation Guide

### Step 1: Install Python

The application requires Python 3.11 or newer.

**Windows:**
1. Download from [python.org](https://www.python.org/downloads/)
2. Run the installer
3. ✅ **Important:** Check "Add Python to PATH"
4. Click "Install Now"

**macOS:**
```bash
# Using Homebrew (recommended)
brew install python@3.11
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv
```

### Step 2: Install Git (Optional but Recommended)

**Windows & macOS:**
Download from [git-scm.com](https://git-scm.com/downloads)

**Linux:**
```bash
sudo apt install git
```

### Step 3: Download the Application

**Option A: Clone from GitHub**
```bash
git clone https://github.com/yourusername/file_organizer.git
cd file_organizer
```

**Option B: Download ZIP**
1. Click the green "Code" button on GitHub
2. Select "Download ZIP"
3. Extract the ZIP file to your desired location
4. Open terminal/command prompt in that folder

### Step 4: Set Up Python Environment

Create a virtual environment to keep dependencies isolated:

**Windows (Command Prompt or PowerShell):**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS & Linux:**
```bash
python3.11 -m venv venv
source venv/bin/activate
```

You should see `(venv)` at the start of your terminal line.

### Step 5: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This installs:
- PyQt6 (desktop application framework)
- Requests (for LLM communication)
- And other supporting libraries

### Step 6: Verify Installation

```bash
python -m pytest tests/ -q
```

You should see: `59 passed` (or similar)

✅ **Installation complete!**

---

## Local LLM Setup

The application can work with different LLM providers. Here's how to set up each one:

### Recommended: Ollama

**Why Ollama?**
- ✅ Easiest to install and use
- ✅ Works on Mac, Windows, Linux
- ✅ Excellent performance on Apple Silicon
- ✅ Large selection of models
- ✅ Completely free
- ✅ Just one tool to manage

#### Installation:

**macOS:**
1. Visit [ollama.ai](https://ollama.ai)
2. Click "Download for Mac"
3. Run the installer
4. Open Applications → Ollama and follow prompts

**Windows:**
1. Visit [ollama.ai](https://ollama.ai)
2. Click "Download for Windows" (requires WSL 2)
3. Follow installation prompts
4. Open "Ollama" from Start Menu

**Linux:**
```bash
curl https://ollama.ai/install.sh | sh
```

#### Running Ollama:

**macOS:**
- Ollama runs automatically in the menu bar
- Look for the Ollama icon at the top of your screen

**Windows & Linux:**
```bash
ollama serve
```

Keep this terminal window open while using the application.

#### Installing a Model:

Open a new terminal (keep Ollama running in the first one) and download a model:

**For Most Users (Recommended):**
```bash
ollama pull llama2
```
- Size: 3.8GB
- Speed: Fast
- Quality: Good
- Memory: 4GB RAM when running

**For Detailed Analysis:**
```bash
ollama pull mistral
```
- Size: 4.1GB
- Speed: Very fast
- Quality: Excellent
- Memory: 4GB RAM when running

**For Apple Silicon (Best Performance):**
```bash
ollama pull neural-chat
```
- Size: 4.0GB
- Speed: Fastest
- Quality: Good
- Memory: 3GB RAM when running

**For Powerful Machines (16GB+ RAM):**
```bash
ollama pull llama2-70b
```
- Size: 39GB
- Speed: Slower but most capable
- Quality: Excellent
- Memory: 12GB RAM when running

#### Check Installation:

```bash
ollama list
```

You should see something like:
```
NAME          ID              SIZE      MODIFIED
llama2        2e8555a25fa1    3.8 GB    2 minutes ago
```

✅ **Ollama is ready to use!**

---

### Alternative: LM Studio

**Why LM Studio?**
- Modern, user-friendly GUI
- Large model selection
- Good for experimentation
- Slightly easier for beginners

#### Installation:

1. Visit [lmstudio.ai](https://lmstudio.ai)
2. Download for your OS
3. Run installer
4. Launch LM Studio

#### Setting Up Models:

1. Click "Search" on the left
2. Find a model (e.g., "mistral-7b")
3. Click download
4. Wait for download to complete

#### Starting the Server:

1. Go to "Local Server" tab
2. Select your model
3. Click "Start Server"

---

### Alternative: LocalAI

**Why LocalAI?**
- Very lightweight
- Good for older computers
- Works with many model formats
- Docker support available

#### Installation (Docker):

```bash
docker run -p 8080:8080 localai/localai:latest
```

#### Getting Models:

```bash
curl -X POST "http://localhost:8080/models/apply" \
  -H "Content-Type: application/json" \
  -d '{"url": "github:go-skynet/model-list/mistral.yaml"}'
```

---

## Application Configuration

### First Launch

1. **Open the Application:**
   ```bash
   python src/main.py
   ```

2. **Settings Window:**
   - Click ⚙️ Settings in the menu
   - Configure your LLM provider

### Configuration Steps:

#### LLM Settings:

1. Click Settings → LLM tab

**If using Ollama:**
- Provider: `ollama`
- Base URL: `http://localhost:11434` (default)
- Model Name: `llama2` (or your installed model)

**If using LM Studio:**
- Provider: `openai-compatible`
- Base URL: `http://localhost:1234/v1`
- Model Name: `local-model`

**If using LocalAI:**
- Provider: `openai-compatible`
- Base URL: `http://localhost:8080/v1`
- Model Name: `gpt-3.5-turbo` (or your model)

#### Organization Settings:

1. Click Settings → Organization tab

**Configure Default Categories:**
- Click "Add Category"
- Examples: Documents, Photos, Videos, Archives, etc.

**File Organization Rules:**
- Choose: Organize by Category or Custom Structure
- Set default directory for organized files

#### General Settings:

1. Click Settings → General tab

**Features:**
- ☑️ Enable automatic backups (recommended: ON)
- ☑️ Enable cache for faster re-analysis (recommended: ON)
- ☑️ Show confirmation before operations (recommended: ON)

**Performance:**
- Max concurrent analyses: `4` (default)
  - Increase to `6-8` if you have 16GB+ RAM
  - Decrease to `2` if you have 8GB RAM

### Saving Configuration:

Click "Save Settings" - your configuration is saved locally.

---

## Using the Application

### Basic Workflow:

#### Step 1: Select Folder

1. Click "📂 Select Folder" or drag and drop a folder
2. Choose the folder containing files to organize
3. The application shows file count and preview

#### Step 2: Analyze Files

1. Click "🔍 Analyze" button
2. Progress bar shows analysis status
3. Application:
   - Reads file content
   - Contacts local LLM for analysis
   - Caches results for future use
   - Shows results in table below

#### Step 3: Review Suggestions

The results table shows:
- **File Name** - Original filename
- **Suggested Category** - Where it should go
- **Suggested Name** - New filename
- **Confidence** - How sure the AI is (0-100%)

**Reviewing Results:**
- ✅ **Green** = High confidence (85%+)
- 🟡 **Yellow** = Medium confidence (60-85%)
- 🔴 **Red** = Low confidence (<60%)

You can:
- Click each row to edit suggestions
- Right-click to remove from organization plan
- Use Cmd/Ctrl+A to select all

#### Step 4: Dry Run (Recommended First Time)

1. Click "⚡ Organize (Dry Run)"
2. See what changes will be made WITHOUT actually making them
3. Review the changes in the output

#### Step 5: Apply Changes

1. If dry run looks good, click "⚡ Organize"
2. Confirm the operation
3. Progress bar shows real-time progress
4. Files are reorganized and renamed

#### Step 6: Undo If Needed

Made a mistake?

1. Click "↩️ Undo Last Operation"
2. All changes are immediately reversed
3. Files return to original names and locations

---

### Advanced Features:

#### Parallel Analysis

The application analyzes multiple files at the same time:
- Settings → General → "Max concurrent analyses"
- Default: `4` (good for most computers)
- Higher = Faster but uses more memory
- Lower = Slower but uses less memory

#### Caching

Analyzed files are cached:
- Same file + same LLM = instant result next time
- Settings → Advanced → View cache statistics
- Clear cache if you want fresh analysis

#### Backup Management

Automatic backups are created:
- Before any file operations
- Stored in: `~/.file_organizer/backups/`
- Kept for 30 days by default
- Click "🔄 Backup" to create manual backup

#### History

View past operations:
- Settings → Advanced → "View operation history"
- See what was changed, when, and by whom
- Option to undo any past operation

---

## Troubleshooting

### Problem: Application Won't Start

**Error: "Module 'src' not found"**

**Solution:**
```bash
# Make sure you're in the right directory
cd /path/to/file_organizer

# Verify Python version
python --version  # Should be 3.11+

# Reinstall dependencies
pip install -r requirements.txt
```

### Problem: LLM Connection Failed

**Error: "Could not connect to Ollama"**

**Checklist:**
1. ✅ Is Ollama running?
   ```bash
   # Check Ollama status
   ollama list
   ```

2. ✅ Correct base URL?
   - Settings → LLM
   - Should be: `http://localhost:11434`

3. ✅ Model installed?
   ```bash
   ollama list  # Should show at least one model
   ```

4. ✅ Firewall blocking?
   - Add application to firewall exceptions
   - Or disable firewall temporarily for testing

**Solution:**
- Restart Ollama
- Check settings are saved
- Try with a simpler model first

### Problem: Analysis is Very Slow

**Possible causes:**
- LLM model too large for your computer
- Not enough RAM available
- Multiple heavy applications running

**Solutions:**
1. **Reduce concurrent analyses:**
   - Settings → General → Max concurrent analyses: `2`

2. **Use a smaller model:**
   ```bash
   ollama pull neural-chat  # Smaller than mistral
   ```

3. **Close other applications**

4. **Check available RAM:**
   - Windows: Ctrl+Shift+Esc → Performance
   - macOS: Activity Monitor
   - Linux: `free -h`

### Problem: Out of Memory Error

**Error: "Not enough memory"**

**Solutions:**
1. **Reduce concurrent analyses to 1 or 2:**
   - Settings → General → Max concurrent analyses: `1`

2. **Reduce file batch size:**
   - Analyze smaller folders (100 files instead of 1000)

3. **Use lighter model:**
   ```bash
   ollama pull neural-chat  # 4GB vs 39GB for llama2-70b
   ```

4. **Upgrade RAM** (if you consistently hit limits)

### Problem: Low Accuracy / Poor Suggestions

**Possible causes:**
- Model not right for your file types
- Files don't have clear content
- Need more specific categories

**Solutions:**
1. **Try different model:**
   ```bash
   ollama pull mistral  # Better reasoning
   ollama pull neural-chat  # Better for documents
   ```

2. **Provide better category hints:**
   - Settings → Organization
   - Define clear, specific categories
   - Add examples in category descriptions

3. **Review suggestions manually:**
   - Edit before applying changes
   - You don't have to accept AI suggestions

4. **Use dry run first:**
   - Always test with dry run before actual changes

---

## Tips & Best Practices

### Before You Start:

1. **Create a backup of your files:**
   ```bash
   # On your own backup system
   cp -r /path/to/files /backup/location
   ```

2. **Test with a small folder first:**
   - Use a test folder with 10-20 files
   - Get comfortable with the workflow

3. **Review AI suggestions carefully:**
   - Edit low-confidence suggestions (< 60%)
   - Use dry run to preview changes

### Organization Strategy:

**Good Category Structure:**
```
Documents/
  - Work
  - Personal
  - Finance
  - Health

Media/
  - Photos
    - Travel
    - Family
    - Projects
  - Videos
  - Music

Projects/
  - Active
  - Archived
  - Templates
```

**Avoid Too Many Categories:**
- More than 10 top-level categories becomes hard to manage
- Use subcategories instead

**Consistent Naming:**
- Decide on naming convention first
  - Examples: `yyyy-mm-dd_description`, `Project_Name_Version`
- Tell the AI about it in settings
- It will be more consistent

### Regular Maintenance:

**Monthly:**
- Review and clean organization structure
- Clear cache if you're using new models
- Check backup storage usage

**Quarterly:**
- Reorganize files if business needs change
- Update category definitions
- Archive old files

**Yearly:**
- Full system audit
- Update to latest models
- Review storage efficiency

### Performance Tips:

1. **Analyze during off-hours:**
   - Run analysis overnight
   - Frees up computer during day

2. **Use cache effectively:**
   - Reanalyze same files only if needed
   - Saves time for repeated operations

3. **Batch operations:**
   - Organize multiple folders at once
   - More efficient than one-by-one

4. **Keep LLM updated:**
   ```bash
   ollama pull llama2  # Gets latest version
   ```

### Privacy & Security:

- ✅ All processing happens locally
- ✅ No data sent to cloud services
- ✅ Backups stored only on your computer
- ✅ Safe to use with sensitive documents

---

## Suggested Enhancements

Based on user feedback and best practices, here are recommended improvements for future versions:

### High Priority (Next Release)

#### 1. **Smart File Preview**
**What:** Show file preview when reviewing suggestions
- **Benefit:** Users can verify AI suggestions before accepting
- **Use Cases:** Quickly check if file categorization makes sense
- **Implementation:** Add preview panel in results table
- **Estimated Impact:** 30% improvement in user confidence

#### 2. **Custom Rules Engine**
**What:** Create files rules that override AI suggestions
- **Rules like:** "All .pdf files with 'invoice' → Finance/Invoices"
- **Benefit:** Automate repetitive patterns, faster processing
- **Use Cases:** Invoices, tax documents, project files
- **Implementation:** Rule builder UI, condition matching engine
- **Estimated Impact:** 40% time savings for power users

#### 3. **Duplicate File Detection**
**What:** Identify and handle duplicate files intelligently
- **Features:** Hash-based duplicate finding
- **Actions:** Delete, keep newest, merge copies
- **Benefit:** Reduces storage, organizes cleaner
- **Implementation:** File hashing, comparison, merge UI
- **Estimated Impact:** Average 15% storage freed

#### 4. **Batch Processing**
**What:** Queue multiple folders for overnight analysis
- **Features:** Schedule analysis, pause/resume, progress tracking
- **Benefit:** Organize without computer running all day
- **Use Cases:** Large photo libraries, document archives
- **Implementation:** Job queue, scheduling module
- **Estimated Impact:** 50% fewer manual operations

#### 5. **Advanced Search & Filter**
**What:** Find files by category, date, confidence level
- **Features:** Full-text search, filters, saved searches
- **Benefit:** Quickly find specific files for review
- **Use Cases:** Finding low-confidence files, recent changes
- **Implementation:** Index building, search UI
- **Estimated Impact:** 25% faster file finding

### Medium Priority (2-3 Releases Out)

#### 6. **Model Recommendation Engine**
**What:** Automatically suggest best model for file types
- **Logic:** Test different models on sample files
- **Benefit:** Users pick optimal model without manual testing
- **Implementation:** Multi-model testing, benchmark comparison
- **Estimated Impact:** 20% accuracy improvement

#### 7. **Collaborative Organization**
**What:** Share organization rules with team members
- **Features:** Export/import rules, shared templates
- **Benefit:** Consistency across team, faster setup
- **Use Cases:** Teams, families, organizations
- **Implementation:** Rule file format, export UI
- **Estimated Impact:** 70% faster team setup

#### 8. **Integration with Cloud Services**
**What:** Organize files on Google Drive, OneDrive, etc.
- **Features:** Direct cloud file organization
- **Benefit:** Organize cloud files without downloading
- **Implementation:** Cloud provider APIs, async uploads
- **Estimated Impact:** Support for 50M+ more users

#### 9. **Mobile App Companion**
**What:** Monitor/control organization from phone
- **Features:** Status updates, pause operations, review suggestions
- **Benefit:** Check progress from anywhere
- **Implementation:** REST API, mobile app
- **Estimated Impact:** Better UX for remote management

#### 10. **AI Training On Your Files**
**What:** Fine-tune model on your specific file types
- **Features:** Learn from your past categorizations
- **Benefit:** Better accuracy over time
- **Implementation:** Model fine-tuning, feedback collection
- **Estimated Impact:** 40% accuracy improvement after 100 files

### Low Priority (Future Enhancements)

#### 11. **Multi-Language Support**
**What:** Translate UI to major languages
- **Impact:** Support international users
- **Benefit:** Accessible to non-English speakers

#### 12. **Workflow Automation**
**What:** Auto-organize on folder watch
- **Features:** Monitor folder, auto-organize new files
- **Benefit:** Hands-off file management
- **Implementation:** File system watcher, scheduled runs

#### 13. **Advanced Analytics Dashboard**
**What:** Visualize file organization patterns
- **Features:** Charts, trends, storage analysis
- **Benefit:** Understand file management habits
- **Implementation:** Data visualization, statistics engine

#### 14. **Integration with Archive Tools**
**What:** Automatically compress old files
- **Features:** Move to archive, compress, manage versions
- **Benefit:** Automatic storage optimization
- **Implementation:** Compression APIs, archive management

#### 15. **OCR for Scanned Documents**
**What:** Extract text from scanned PDFs/images
- **Features:** Tesseract OCR integration
- **Benefit:** Organize scans intelligently
- **Implementation:** OCR pipeline, confidence tracking

---

## Common Questions

### Q: Is my data safe?
**A:** Yes! All processing happens locally on your computer. No data is sent to cloud services or external servers. Your files never leave your computer.

### Q: Can I use this with OneDrive/Google Drive?
**A:** Currently, files must be on your local computer. Cloud integration is planned for a future release.

### Q: What if I disagree with the AI suggestions?
**A:** You can edit any suggestion before applying changes. Use "Dry Run" to preview changes first.

### Q: How much disk space do I need?
**A:** About 5GB minimum (application + LLM). If you organize many files, add space for backups (typically 10-20% of organized files).

### Q: Can I undo changes after I close the app?
**A:** Yes! Undo works even after closing and reopening the app. History is stored in the database for 30 days.

### Q: How do I pick the right LLM model?
**A:** Start with `llama2` (good balance) or `mistral` (faster but smaller). Test with 10 files first to see quality/speed tradeoff.

### Q: Can I use multiple LLM models?
**A:** Currently one at a time. Switching is as simple as changing settings. Multiple model support is planned.

### Q: What if I have very old/unusual file formats?
**A:** The application handles 40+ text formats, PDFs, Office documents, and images. Unknown formats are analyzed as generic files - it works but with less detail.

---

## Getting Help

### Documentation:
- 📖 [README.md](README.md) - Project overview
- 🔧 [SETUP.md](SETUP.md) - Detailed setup instructions
- 📋 [PRD.md](PRD_AI_File_Organizer.md) - Full feature specifications

### Community:
- 🐙 GitHub Issues - Report bugs
- 💬 GitHub Discussions - Ask questions
- 📧 Email support (if available)

### Reporting Issues:

When reporting a bug, include:
1. Operating system (Windows/macOS/Linux)
2. Python version (`python --version`)
3. LLM model being used (`ollama list`)
4. Exact error message
5. Steps to reproduce

---

## Roadmap

**Current:** Phase 4 Complete (Caching, Parallel Processing)

**Next Quarter:**
- Smart file preview
- Custom rules engine
- Duplicate detection
- Batch processing

**Future:**
- Cloud integration
- Mobile companion
- Multi-language support
- Advanced analytics

---

**Last Updated:** January 30, 2026  
**Version:** 1.0  
**Status:** Production Ready

For the latest updates, visit the GitHub repository or check the application's Help menu.
