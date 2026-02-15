# Quick Start: Local LLM Setup Guide

**For:** AI File Organizer  
**Date:** January 2026  
**Duration:** 15-30 minutes

---

## TL;DR (Too Long; Didn't Read)

1. Install Ollama: [ollama.ai](https://ollama.ai)
2. Download a model: `ollama pull llama2`
3. Keep it running: `ollama serve`
4. Configure app: Settings → LLM → `http://localhost:11434`, model: `llama2`
5. Done! ✅

---

## Why Local LLM?

✅ **Privacy** - Your files never leave your computer  
✅ **Speed** - Instant processing, no internet needed  
✅ **Cost** - Free (no API charges)  
✅ **Control** - Complete control over your data  
✅ **Works Offline** - Use anywhere, anytime  

---

## Installation (Choose One)

### Option 1: Ollama (Easiest) ⭐ Recommended

**macOS:**
1. Download: [ollama.ai/download](https://ollama.ai/download)
2. Open DMG file
3. Drag to Applications
4. Open Applications → Ollama
5. Grant permissions when asked

**Windows:**
1. Download: [ollama.ai/download](https://ollama.ai/download)
2. Run installer
3. Restart computer
4. Open "Ollama" from Start Menu

**Linux:**
```bash
curl https://ollama.ai/install.sh | sh
```

### Option 2: LM Studio (GUI Alternative)

1. Download: [lmstudio.ai](https://lmstudio.ai)
2. Install and run
3. Click "Search"
4. Download a model
5. Go to "Local Server" → Start

### Option 3: LocalAI (Docker)

```bash
docker run -p 8080:8080 localai/localai:latest
```

---

## Download a Model

### Using Ollama:

Open terminal and run:

```bash
# Most popular (balanced)
ollama pull llama2

# Faster
ollama pull neural-chat

# Better reasoning (slightly slower)
ollama pull mistral

# Most capable (very large, slow)
ollama pull llama2-70b
```

Check what you have:
```bash
ollama list
```

### Using LM Studio:

1. Click "Search" in left sidebar
2. Search for a model (e.g., "mistral")
3. Click the download arrow
4. Wait for completion (will show in "Local Models")

---

## Keep LLM Running

### Ollama (Automatic):

On **macOS**: Runs automatically in background  
On **Windows**: Runs automatically  
On **Linux**: Run in terminal:
```bash
ollama serve
```

### LM Studio:

1. Click "Local Server" tab
2. Select model from dropdown
3. Click "Start Server"
4. You'll see "Listening on http://localhost:1234"

### LocalAI:

Already running if you started Docker container. Check:
```bash
curl http://localhost:8080/v1/models
```

---

## Configure AI File Organizer

### Step 1: Open Settings

1. Launch AI File Organizer
2. Click ⚙️ **Settings** menu

### Step 2: Go to LLM Tab

Click **LLM** in the settings tabs

### Step 3: Configure for Your Setup

#### If Using Ollama:
```
Provider: ollama
Base URL: http://localhost:11434
Model Name: llama2 (or your model name)
Max Tokens: 500
Temperature: 0.7
```

#### If Using LM Studio:
```
Provider: openai-compatible
Base URL: http://localhost:1234/v1
Model Name: local-model
Max Tokens: 500
Temperature: 0.7
```

#### If Using LocalAI:
```
Provider: openai-compatible
Base URL: http://localhost:8080/v1
Model Name: gpt-3.5-turbo (or your model)
Max Tokens: 500
Temperature: 0.7
```

### Step 4: Save

Click **Save Settings**

### Step 5: Test

1. Select a folder with some files
2. Click **Analyze**
3. You should see results within 10-30 seconds (depends on model)

---

## Model Comparison

### Choosing the Right Model

| Model | Size | Speed | Quality | RAM | Best For |
|-------|------|-------|---------|-----|----------|
| **neural-chat** | 4.0GB | ⚡⚡⚡ Fastest | Good | 3GB | Speed (default start) |
| **llama2** | 3.8GB | ⚡⚡ Fast | Good | 4GB | All-around best |
| **mistral** | 4.1GB | ⚡⚡ Fast | Excellent | 4GB | Accuracy focused |
| **dolphin-mixtral** | 26GB | ⚡ Medium | Excellent | 10GB | Top quality |
| **llama2-70b** | 39GB | 🐢 Slow | Best | 12GB+ | Maximum capability |

### Quick Recommendation:

**Just starting out?** → `neural-chat` (fastest)  
**Want best balance?** → `llama2` (most popular)  
**Need accuracy?** → `mistral` (best reasoning)  
**Have powerful computer?** → `dolphin-mixtral` (best quality)  

---

## Verify It's Working

### Test Ollama:

```bash
curl http://localhost:11434/api/tags
```

You should see your models listed.

### Test LM Studio:

Visit in browser: `http://localhost:1234`

### Test LocalAI:

```bash
curl http://localhost:8080/v1/models
```

---

## Performance Tips

### Speed Up Analysis:

1. **Use smaller model:**
   ```bash
   ollama pull neural-chat  # ~3s per file
   ```

2. **Reduce concurrent analyses:**
   - Settings → General → Max concurrent: `2`

3. **Optimize model settings:**
   - Settings → LLM → Temperature: `0.3` (faster, less creative)
   - Max Tokens: `200` (shorter responses)

4. **Disable cache clearing:**
   - Settings → Advanced → Cache retention: `∞`

### Better Accuracy:

1. **Use larger model:**
   ```bash
   ollama pull mistral
   ```

2. **Increase temperature:**
   - Settings → LLM → Temperature: `0.9` (more creative)

3. **Increase max tokens:**
   - Max Tokens: `500` (more detailed)

### Reduce Memory Usage:

1. **Close other apps**
2. **Reduce concurrent analyses:**
   - Settings → General → Max concurrent: `1`
3. **Use smaller model:**
   ```bash
   ollama pull neural-chat
   ```

---

## Troubleshooting

### Error: "Could not connect to LLM"

**Check Ollama is running:**
```bash
# macOS: Should see Ollama in menu bar
# Windows: Should see Ollama.exe running
# Linux:
ollama serve  # in a terminal
```

**Check URL is correct:**
- Ollama default: `http://localhost:11434`
- LM Studio default: `http://localhost:1234/v1`
- LocalAI default: `http://localhost:8080/v1`

**Check model exists:**
```bash
ollama list
```

### Error: "Out of Memory"

Solutions:
1. Close other applications
2. Use smaller model: `ollama pull neural-chat`
3. Reduce concurrent analyses: Settings → General → Max concurrent: `1`

### Analysis is Very Slow

If analysis takes >30 seconds per file:
1. Model may be too large
2. Computer may be overloaded
3. Try: Settings → General → Max concurrent: `1`

---

## Updating Models

Keep your models up to date:

```bash
ollama pull llama2  # Updates to latest version
```

Check version:
```bash
ollama list
```

---

## Memory Requirements

What to expect for your computer:

| Model | Download | RAM Used | Speed |
|-------|----------|----------|-------|
| neural-chat | 4.0GB | 3GB | 3-5 sec/file |
| llama2 | 3.8GB | 4GB | 5-8 sec/file |
| mistral | 4.1GB | 4GB | 4-6 sec/file |
| dolphin-mixtral | 26GB | 10GB | 10-15 sec/file |
| llama2-70b | 39GB | 12GB | 20-30 sec/file |

**Tip:** Check your RAM:
- macOS: Apple menu → About This Mac
- Windows: Ctrl+Shift+Esc → Performance
- Linux: `free -h`

---

## Next Steps

1. ✅ Install Ollama / LM Studio / LocalAI
2. ✅ Download a model
3. ✅ Keep it running
4. ✅ Configure in AI File Organizer
5. 🎉 Start organizing files!

---

## Still Need Help?

### Common Questions:

**Q: Which model should I use?**  
A: Start with `neural-chat` (fastest) or `llama2` (most popular). Test both!

**Q: Does it work without internet?**  
A: Yes! After downloading the model, everything runs locally.

**Q: Can I use multiple models?**  
A: One at a time. Easy to switch in settings.

**Q: How much disk space?**  
A: Models are 4-40GB depending on size.

**Q: Can I use OpenAI's API instead?**  
A: Yes! But then your data goes to cloud. Not recommended for privacy.

---

## Learn More

- **Ollama Models:** [ollama.ai/library](https://ollama.ai/library)
- **LM Studio:** [lmstudio.ai](https://lmstudio.ai)
- **LocalAI:** [localai.io](https://localai.io)
- **App Documentation:** See `USER_GUIDE.md`

---

**Version:** 1.0  
**Last Updated:** January 2026  
**Status:** Ready to Use
