# 🤖 Claude API Setup Guide

This guide walks you through setting up the Claude API for the AI-powered fixer.

## Step 1: Get Your API Key

1. **Visit Anthropic Console**: https://console.anthropic.com/
2. **Sign up or login** (free trial available)
3. **Click "API Keys"** in the left sidebar
4. **Create new API key** - Copy it (starts with `sk-ant-`)
5. **Keep it secret!** Never share this key publicly

## Step 2: Configure Your App

### Option A: Using .env file (Recommended)

```bash
# 1. Navigate to appsec_final folder
cd appsec_final

# 2. Create .env file (or edit existing one)
# Windows:
copy .env.example .env
# Then edit .env with your text editor

# 3. Find the line:
CLAUDE_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 4. Replace with your actual key:
CLAUDE_API_KEY=sk-ant-abc123def456...
```

### Option B: Using Environment Variable

```bash
# Windows Command Prompt:
set CLAUDE_API_KEY=sk-ant-your-key-here
python run.py

# Windows PowerShell:
$env:CLAUDE_API_KEY="sk-ant-your-key-here"
python run.py
```

## Step 3: Verify Setup

```bash
# Start the app
python run.py

# You should see:
# ==================================================
#   AppSec Orchestrator
#   http://localhost:5000
# ==================================================
```

If you see errors about CLAUDE_API_KEY, the key wasn't set correctly.

## Step 4: Test AI Fixer

1. Open http://localhost:5000
2. Register account
3. Create a project with a Python file containing:
   ```python
   api_key = "sk-1234567890abcdef"
   ```
4. Run scan → Find "Hardcoded Secrets"
5. Click "Generate Fix" → Should use AI to fix it
6. Review the fix → Click "Apply"

## ✅ Success Signs

- "✨ Fix generated with AI" message appears
- Diff shows the fix
- "✅ Applied successfully" after clicking Apply

## ❌ Troubleshooting

### Error: "CLAUDE_API_KEY not set"
- Check .env file exists and has your key
- Make sure line isn't commented out (#)
- Restart the app after editing .env

### Error: "anthropic package not installed"
```bash
pip install anthropic
```

### Error: "Unauthorized" (401)
- Your API key is wrong or expired
- Generate a new key from console.anthropic.com
- Update .env and restart

### API calls are slow
- Claude API can take 5-10 seconds per fix
- This is normal for AI inference
- Faster for pattern-matched fixes (instant)

## 📊 Pricing

Claude API usage is **pay-per-use**:
- ~$0.003 per 1K input tokens (code to analyze)
- ~$0.015 per 1K output tokens (generated fix)
- Example: 1 fix ≈ $0.01-0.05

**Free tier**: New accounts get $5 credit to test

## 🔐 Security

- API key is **not stored** anywhere except your .env
- .env is in .gitignore (won't be committed to git)
- All fixes happen locally - files never sent to Anthropic except context
- Anthropic doesn't train on your code by default

## Advanced: Disable AI Fixer

If you want to use only pattern-based fixes (no API calls):

```bash
# In .env:
ENABLE_AI_FIXER=0
```

This will disable Claude API calls and use only fast pattern matching.

## Need Help?

- Anthropic Docs: https://docs.anthropic.com/
- Status Page: https://status.anthropic.com/
- Contact: support@anthropic.com

---

Once configured, your app can intelligently fix **any** code vulnerability! 🎉
