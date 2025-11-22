# 🔧 KB Builder Troubleshooting Guide

## Issue: Blank Agent Replies on 2nd PC

If the KB Builder shows blank replies on one PC but works on another, follow these steps:

---

## ✅ Step 1: Verify API Key

**Check if your `.env` file exists and has the correct API key:**

```bash
cd demo
# Check if .env exists
ls .env  # Linux/Mac
dir .env  # Windows

# View contents (be careful not to share!)
cat .env  # Linux/Mac
type .env  # Windows
```

**Your `.env` should contain:**
```
OPENAI_API_KEY=sk-your-actual-api-key-here
OPENAI_MODEL=gpt-5-mini
OPENAI_REASONING_EFFORT=low
```

**If missing, create it:**
```bash
cp .env.example .env
# Then edit .env and add your API key
```

---

## ✅ Step 2: Check Python/OpenAI Library Version

**Different library versions can cause issues. Check versions:**

```bash
python --version  # Should be 3.11+
pip show openai
```

**Update if needed:**
```bash
pip install --upgrade openai>=2.0.0
pip install --upgrade python-dotenv
```

---

## ✅ Step 3: Test API Connection

**Create a test script to verify API works:**

Create `test_api.py` in the `demo` folder:

```python
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("❌ ERROR: OPENAI_API_KEY not found in .env file")
    exit(1)

print(f"✅ API Key found: {api_key[:10]}...")

try:
    client = OpenAI(api_key=api_key)
    response = client.responses.create(
        model="gpt-5-mini",
        input="Say hello",
        reasoning={"effort": "low"}
    )
    
    # Check response structure
    print(f"✅ API call successful!")
    print(f"Response type: {type(response)}")
    print(f"Response attributes: {dir(response)}")
    
    # Try to get text
    if hasattr(response, 'output_text'):
        print(f"✅ output_text found: {response.output_text[:50]}...")
    elif hasattr(response, 'text'):
        print(f"✅ text found: {response.text[:50]}...")
    else:
        print(f"⚠️  No text attribute found. Full response: {response}")
        
except Exception as e:
    print(f"❌ API Error: {str(e)}")
```

**Run it:**
```bash
python test_api.py
```

---

## ✅ Step 4: Check Streamlit Console

**When running the KB Builder, check the console for errors:**

```bash
streamlit run unified_kb_system.py
```

**Look for:**
- API errors
- Import errors
- Attribute errors
- Network timeouts

---

## ✅ Step 5: Enable Debug Mode

**Add debug logging to see what's happening:**

The code now includes better error handling. If you still see blank replies:

1. **Check the browser console** (F12 → Console tab) for JavaScript errors
2. **Check Streamlit logs** in the terminal
3. **Try a simple query** like "hello" or "list articles"

---

## ✅ Step 6: Common Issues & Fixes

### Issue: "OPENAI_API_KEY not set"
**Fix:** Create `.env` file with your API key

### Issue: "AttributeError: 'Response' object has no attribute 'output_text'"
**Fix:** Update OpenAI library: `pip install --upgrade openai`

### Issue: "API rate limit exceeded"
**Fix:** Check your OpenAI account for credits/rate limits

### Issue: "Network timeout"
**Fix:** Check internet connection, try again

### Issue: Blank responses but no errors
**Fix:** 
1. Check if response object has different structure
2. Try updating the code (latest version has better fallbacks)
3. Check if API key has proper permissions

---

## ✅ Step 7: Compare Working vs Non-Working PC

**Check differences between the two PCs:**

1. **Python version:**
   ```bash
   python --version
   ```

2. **OpenAI library version:**
   ```bash
   pip show openai
   ```

3. **Other dependencies:**
   ```bash
   pip list | grep -i openai
   pip list | grep -i streamlit
   ```

4. **Environment variables:**
   ```bash
   # Check if .env is being loaded
   python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('API Key:', 'SET' if os.getenv('OPENAI_API_KEY') else 'NOT SET')"
   ```

---

## ✅ Step 8: Reinstall Dependencies

**If nothing else works, reinstall:**

```bash
cd demo
pip install --upgrade -r requirements.txt
```

**Or fresh install:**
```bash
pip uninstall openai python-dotenv streamlit
pip install openai>=2.0.0 python-dotenv>=1.0.0 streamlit>=1.28.0
```

---

## 🐛 Debug Information to Collect

If the issue persists, collect this info:

1. **Python version:** `python --version`
2. **OpenAI version:** `pip show openai`
3. **Error message** (if any) from console
4. **Response object structure** (from test_api.py)
5. **Whether API key is detected:** Run the test script above

---

## 💡 Quick Fix Checklist

- [ ] `.env` file exists in `demo/` folder
- [ ] `.env` contains valid `OPENAI_API_KEY`
- [ ] OpenAI library is up to date (`pip install --upgrade openai`)
- [ ] Python version is 3.11+
- [ ] Internet connection is working
- [ ] API key has credits available
- [ ] No firewall blocking API calls
- [ ] Try running `test_api.py` to verify API works

---

## 📞 Still Not Working?

If blank replies persist after trying all steps:

1. **Check the latest code** - Make sure you've pulled the latest changes:
   ```bash
   git pull origin main
   ```

2. **The latest code includes:**
   - Better error handling
   - Fallback for missing `output_text` attribute
   - Better error messages
   - Debug logging

3. **Try the test script** to see what the API actually returns

4. **Compare response structures** between working and non-working PCs

---

**The latest code update should fix most issues with blank replies by:**
- ✅ Safely extracting response text from multiple possible attributes
- ✅ Providing fallback messages when response is empty
- ✅ Better error handling and logging
- ✅ Clearer error messages for users

