# 🔐 Setting Up API Key on a New PC

Since `.env` files are **never committed to GitHub** (for security), you'll need to set it up manually on each new machine.

---

## ✅ Method 1: Copy from Your Current PC (Recommended)

### On Your Current PC:
1. Open `demo/.env` file
2. Copy the entire contents

### On the New PC:
1. Clone the repository:
   ```bash
   git clone https://github.com/orizktaillandier/TAC---AI-project.git
   cd TAC---AI-project/demo
   ```

2. Create `.env` file:
   ```bash
   # Option A: Copy from template and edit
   cp .env.example .env
   # Then paste your API key into the file
   
   # Option B: Create directly
   # Create .env file and paste your API key
   ```

3. Paste your API key into the `.env` file:
   ```
   OPENAI_API_KEY=sk-your-actual-api-key-here
   OPENAI_MODEL=gpt-5-mini
   OPENAI_REASONING_EFFORT=low
   ```

---

## ✅ Method 2: Use a Password Manager

1. Store your API key in a password manager (1Password, LastPass, Bitwarden, etc.)
2. On the new PC, retrieve it from your password manager
3. Create `.env` file and paste the key

---

## ✅ Method 3: Secure Transfer

### Option A: Encrypted Message
- Send yourself the API key via encrypted message (Signal, encrypted email, etc.)
- Copy it on the new PC

### Option B: USB Drive
- Copy `.env` file to a USB drive
- Transfer to new PC (make sure to delete from USB after)

### Option C: Cloud Storage (Encrypted)
- Upload `.env` to encrypted cloud storage (only you have access)
- Download on new PC
- Delete from cloud after transfer

---

## ✅ Method 4: Use Environment Variables (Advanced)

Instead of a `.env` file, you can set environment variables directly:

### Windows (PowerShell):
```powershell
$env:OPENAI_API_KEY="sk-your-actual-api-key-here"
$env:OPENAI_MODEL="gpt-5-mini"
$env:OPENAI_REASONING_EFFORT="low"
```

### Windows (Command Prompt):
```cmd
set OPENAI_API_KEY=sk-your-actual-api-key-here
set OPENAI_MODEL=gpt-5-mini
set OPENAI_REASONING_EFFORT=low
```

### Linux/Mac:
```bash
export OPENAI_API_KEY="sk-your-actual-api-key-here"
export OPENAI_MODEL="gpt-5-mini"
export OPENAI_REASONING_EFFORT="low"
```

---

## 🚨 Security Best Practices

1. **Never commit `.env` to git** ✅ (Already protected by `.gitignore`)
2. **Don't share API keys in plain text** - Use encrypted methods
3. **Use different API keys for different environments** (dev, staging, prod)
4. **Rotate keys periodically** if you suspect they're compromised
5. **Delete `.env` from USB/cloud after transfer**

---

## 📝 Quick Checklist for New PC

- [ ] Clone repository from GitHub
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Create `.env` file (copy from `.env.example` or create manually)
- [ ] Add your API key to `.env`
- [ ] Test: `streamlit run unified_kb_system.py`
- [ ] Verify it works!

---

## 💡 Pro Tip

If you're setting up multiple machines frequently, consider:
- Using a password manager (easiest)
- Creating a secure note with your API key
- Using environment variables if you're comfortable with them

---

**Remember: Your API key is like a password - keep it secret! 🔒**

