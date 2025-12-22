# Wiko Defect Analyzer - Complete Testing Guide

## 🎯 All Issues Have Been Fixed!

### Fixed Issues:
1. ✅ GPT-5.2 analyzer now uses `max_completion_tokens` instead of `max_tokens`
2. ✅ API endpoint properly saves uploaded images to temp files
3. ✅ Enum case sensitivity fixed (handles both uppercase and lowercase)
4. ✅ Flask routes properly handle async analyzer calls

---

## 🚀 Step-by-Step Startup Instructions

### Terminal 1: Start Backend Server

```bash
cd "/Users/tonyadmin/wiko-defect-analyzer 2"
./start_server.sh
```

**Expected Output:**
```
╔═══════════════════════════════════════════════════════════╗
║     WIKO DEFECT ANALYZER API                              ║
║     Manufacturing Intelligence Platform                    ║
╠═══════════════════════════════════════════════════════════╣
║  Endpoints:                                                ║
║    POST /api/v1/analyze        - Single image analysis    ║
║    POST /api/v1/analyze/batch  - Batch analysis           ║
║    POST /api/v1/shift-report   - Generate shift report    ║
║    GET  /api/v1/defect-types   - List defect types        ║
║    GET  /api/v1/production-stages - Production flow       ║
║    GET  /api/v1/facilities     - Wiko facilities          ║
╚═══════════════════════════════════════════════════════════╝
 * Serving Flask app 'app'
 * Running on http://0.0.0.0:5001
```

### Terminal 2: Start Frontend

```bash
cd "/Users/tonyadmin/wiko-defect-analyzer 2"
npm run dev
```

**Expected Output:**
```
VITE v5.x.x  ready in xxx ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
```

### Terminal 3: Run Test Suite

```bash
cd "/Users/tonyadmin/wiko-defect-analyzer 2"
./test_api.sh
```

---

## 🧪 Test Scripts Available

### 1. `test_gpt52_direct.py` - Test Azure GPT-5.2 Connection
Tests the Azure OpenAI API connection directly.

```bash
source venv/bin/activate
python3 test_gpt52_direct.py
```

**What it tests:**
- ✓ Azure endpoint configuration
- ✓ API key validity
- ✓ GPT-5.2 deployment accessibility
- ✓ Basic completion request

### 2. `test_api.sh` - Complete API Test Suite
Comprehensive tests for all endpoints.

```bash
./test_api.sh
```

**What it tests:**
- ✓ Health check endpoint
- ✓ Defect types endpoint
- ✓ Production stages endpoint
- ✓ **Full image analysis with GPT-5.2** (uploads test_knife.jpg)

### 3. Manual curl Test

```bash
curl -X POST http://localhost:5001/api/v1/analyze \
  -F "image=@test_knife.jpg" \
  -F "product_sku=WK-KN-200" \
  -F "facility=yangjiang"
```

---

## 🌐 Frontend Testing

### How to Test:

1. Open browser to http://localhost:5173
2. Upload a knife photo (or use `test_knife.jpg`)
3. Select Product SKU (default: WK-KN-200)
4. Select Facility (default: Yangjiang Production)
5. Click **"Analyze for Defects"**
6. Wait for GPT-5.2 analysis (15-30 seconds)

### Check Browser Console:

Press `F12` → Console tab to see:
- Network requests to `/api/v1/analyze`
- Response data from GPT-5.2
- Any JavaScript errors

### Expected Analysis Result:

```json
{
  "success": true,
  "analysis": {
    "defect_id": "DEF-20251222-XXXXXXXX",
    "timestamp": "2025-12-22T...",
    "facility": "yangjiang",
    "product_sku": "WK-KN-200",
    "defect_detected": true/false,
    "defect_type": "blade_scratch | rust_spot | unknown | ...",
    "severity": "critical | major | minor | cosmetic",
    "confidence": 0.85,
    "description": "Detailed defect description...",
    "affected_area": "blade | edge | handle | ...",
    "probable_stage": "vacuum_quench | blade_glazing | ...",
    "root_cause": "Root cause statement...",
    "five_why_chain": ["Why 1", "Why 2", ...],
    "contributing_factors": ["Factor 1", "Factor 2", ...],
    "corrective_actions": ["Immediate action 1", ...],
    "preventive_actions": ["Long-term action 1", ...],
    "reasoning_tokens_used": 12345,
    "model_version": "gpt-5.2"
  }
}
```

---

## 📊 What GPT-5.2 Does

### Vision + Classification Agent (High Reasoning)
- Analyzes image for visual defects
- Identifies defect type and affected area
- Classifies severity level
- Provides confidence score

### Root Cause Analysis Agent (xhigh Reasoning)
- Performs 5-Why analysis
- Creates Ishikawa (fishbone) diagram
- Identifies probable production stage
- Lists contributing factors

### Reporting Agent
- Generates corrective actions (immediate)
- Generates preventive actions (long-term)
- Provides quality check recommendations

---

## 🔍 Troubleshooting

### Issue: "Analysis doesn't work"

**Check these in order:**

1. **Is Flask server running?**
   ```bash
   curl http://localhost:5001/health
   ```
   Should return: `{"status":"healthy",...}`

2. **Check Flask terminal logs**
   Look for errors when you upload an image

3. **Check browser console (F12)**
   - Go to Console tab
   - Look for red errors
   - Go to Network tab
   - Find the `/api/v1/analyze` request
   - Check the response

4. **Test API directly:**
   ```bash
   ./test_api.sh
   ```

### Issue: "ModuleNotFoundError: No module named 'flask'"

**Solution:** Always use the virtual environment:
```bash
source venv/bin/activate
python3 app.py
```

Or use the startup script:
```bash
./start_server.sh
```

### Issue: "Connection refused" or "Port already in use"

**Check if server is already running:**
```bash
ps aux | grep "python.*app.py"
```

**Kill existing server:**
```bash
pkill -f "python.*app.py"
```

**Then restart:**
```bash
./start_server.sh
```

---

## 📝 Key Files Created

- `start_server.sh` - Easy Flask server startup
- `test_api.sh` - Complete API test suite
- `test_gpt52_direct.py` - Azure GPT-5.2 connection test
- `test_knife.jpg` - Sample test image
- `TESTING_GUIDE.md` - This guide

---

## 🎉 Success Indicators

You'll know everything is working when:

✅ Flask server starts without errors
✅ Frontend loads at http://localhost:5173
✅ `test_api.sh` passes all tests
✅ Browser shows "Analyzing with GPT-5.2..." when you upload
✅ Results appear in the frontend after 15-30 seconds
✅ Flask terminal shows: `POST /api/v1/analyze HTTP/1.1" 200`

---

## 💡 Tips

- GPT-5.2 analysis takes **15-30 seconds** (this is normal!)
- The model uses **high reasoning** for vision and **xhigh** for RCA
- Watch Flask terminal for real-time progress
- Use test_knife.jpg for quick testing
- Check AZURE_AI_API_KEY in .env if you get auth errors

---

## 🆘 Need Help?

1. Run `./test_api.sh` to diagnose
2. Check Flask server terminal output
3. Check browser console (F12)
4. Verify .env file has correct Azure credentials

**Ready to test!** 🚀
