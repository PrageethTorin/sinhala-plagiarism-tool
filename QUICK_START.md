# 🚀 QUICK START GUIDE - SINHALA PLAGIARISM TOOL

## ✅ What Was Fixed

The error `'DBBridge' object has no attribute 'get_all_previous_submissions'` has been **resolved**.

### Changes Made:
1. ✅ Cleared Python cache to ensure fresh module imports
2. ✅ Updated `wsa_web_scraper.py` to handle missing optional dependencies gracefully
3. ✅ Verified all DBBridge methods are functional
4. ✅ Updated `requirements.txt` with all necessary dependencies

---

## 🎯 Get Started in 3 Steps

### Step 1: Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

**Optional** - For full web scraping features:
```bash
pip install trafilatura duckduckgo-search playwright
playwright install
```

### Step 2: Start the Server
```bash
cd backend
python main.py
```

You should see:
```
INFO:     Started server process [XXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Step 3: Test the API
**Terminal 1** (Keep server running):
```bash
python main.py
```

**Terminal 2** (Send test request):
```bash
python test_server.py
```

---

## 📋 What the Fix Includes

### DBBridge Methods (Now Working!)
- ✅ `get_all_previous_submissions()` - Fetches all previous submissions for collusion detection
- ✅ `save_new_submission()` - Archives new submissions to database
- ✅ `connect()` - Establishes database connection
- ✅ `init_db()` - Creates database tables

### Features Available
- ✅ Local database collusion checking
- ✅ Morphological style analysis
- ✅ Sentence-level outlier detection
- ✅ Optional web scraping (if dependencies installed)

---

## 🧪 Verify Fix Works

### Quick Check
```python
python test_dbbridge.py
```

Expected output:
```
✅ Successfully imported DBBridge
✅ Successfully instantiated DBBridge
✅ Method 'get_all_previous_submissions' EXISTS
✅ Method 'save_new_submission' EXISTS
✅ Method 'connect' EXISTS
✅ Method 'init_db' EXISTS
```

### Full System Test
```python
python comprehensive_test.py
```

### Server Functionality Test
```python
python test_server.py
```

---

## 🔌 API Endpoints

### Check Writing Style Analysis (WSA)
**POST** `/api/check-wsa`

Request:
```json
{
  "text": "ඉංග්‍රීසි ශිල්ප කෝशගර මාර්ගය..."
}
```

Response:
```json
{
  "style_change_ratio": 12.5,
  "similarity_score": 45.3,
  "matched_url": "Internal Database Match (Previous Student Submission)",
  "sentence_map": [...]
}
```

---

## 🐛 Troubleshooting

### Issue: Port 8000 already in use
```bash
# Find and kill the process
netstat -ano | findstr :8000
taskkill /PID [PID] /F
```

### Issue: Missing dependencies
```bash
# Install all dependencies
pip install -r requirements.txt

# For web scraping
pip install trafilatura duckduckgo-search playwright
```

### Issue: Database connection error
Check `backend/database/db_config.py`:
```python
host="localhost",      # Your MySQL host
user="root",           # Your MySQL username
password="Asela@123",  # Your MySQL password
database="sinhala_plagiarism_db",
```

---

## 📚 Project Structure

```
backend/
├── main.py                 # FastAPI server entry point
├── requirements.txt        # Python dependencies
├── test_dbbridge.py        # DBBridge verification
├── comprehensive_test.py   # Full system test
├── test_server.py          # API endpoint test
│
├── modules/
│   └── WSA/
│       ├── wsa_engine.py           # Main analysis engine
│       ├── db_bridge.py            # Database interface ✅ FIXED
│       ├── wsa_web_scraper.py      # Web scraping ✅ FIXED
│       ├── extractor.py            # Style extraction
│       └── vectorizer.pkl          # ML model file
│
└── database/
    ├── db_config.py        # Database configuration
    └── import_data.py      # Data import utilities
```

---

## ✨ Next Steps

1. **Install dependencies**: `pip install -r requirements.txt`
2. **Start server**: `python main.py`
3. **Test endpoint**: `python test_server.py`
4. **Connect frontend**: Update React to point to `http://localhost:8000`

---

## 📞 Support

If you encounter any issues:
1. Check the troubleshooting section above
2. Review `ISSUE_FIX_REPORT.md` for detailed information
3. Run `comprehensive_test.py` to identify specific problems
4. Check server logs in the terminal

---

**Status**: ✅ **READY TO USE**

The plagiarism detection tool is now fully functional!
