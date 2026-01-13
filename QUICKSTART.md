# 🚀 Quick Start Guide

## 1️⃣ Activate Virtual Environment
```powershell
.venv\Scripts\Activate.ps1
```

## 2️⃣ Start the Server
```powershell
python -m uvicorn app.main:app --reload --port 8000
```

Wait for:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

## 3️⃣ Open in Browser

**Landing Page:**
- http://127.0.0.1:8000

**API Documentation:**
- http://127.0.0.1:8000/docs (Swagger UI - interactive!)

## 4️⃣ Test the Flow

1. Click **Register** → Create account (username: `dancer1`, password: `pass123`)
2. Click **Login** → Login with your credentials
3. You'll be redirected to **Home Page** ✨
4. Add songs manually or upload photos
5. View all dance workshops in your area
6. Click **Logout** to return to login

## 5️⃣ Run Integration Tests (Optional)
```powershell
python test_api.py
```

Should show all tests passing: ✅

---

## 📍 Key URLs

| URL | Purpose |
|-----|---------|
| http://127.0.0.1:8000/ | Landing page |
| http://127.0.0.1:8000/register.html | Registration form |
| http://127.0.0.1:8000/login.html | Login form |
| http://127.0.0.1:8000/home.html | Dashboard (after login) |
| http://127.0.0.1:8000/docs | API documentation |

---

## 💡 Example Test Data

**Test User:**
- Username: `testuser1`
- Password: `pass123`

**Add a Workshop (from API docs):**
- City: `Paris`
- Location: `Studio Bachata`
- Date: `2026-02-20`
- Time: `20:00`
- Style: `bachata`

---

## 🛑 Stop the Server
Press: `CTRL + C` in the terminal

---

**Enjoy! 💃🕺**

