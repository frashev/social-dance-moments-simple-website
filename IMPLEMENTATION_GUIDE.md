# SDM Web App - Implementation Guide

## ✅ Status: Phase 2 Complete!

Successfully built a full-stack web app with user registration/login, song recommendations, and dance workshops map.

---

## 📁 Project Structure

```
PythonBasics/
├── app/                      # Backend (FastAPI)
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── auth.py              # User registration/login
│   ├── recommend.py         # Song recommendation endpoints
│   ├── workshops.py         # Workshop CRUD endpoints
│   ├── database.py          # SQLite connection & schema
│   ├── models.py            # Pydantic data models
│   ├── utils.py             # Password hashing (argon2)
│   └── init_db.py           # DB initialization script
├── frontend/                # Frontend (HTML/CSS/JS)
│   ├── index.html           # Landing page
│   ├── register.html        # User registration form
│   ├── login.html           # User login form
│   └── home.html            # User dashboard (songs & workshops)
├── dance_app.db             # SQLite database (auto-created)
├── requirements.txt         # Python dependencies
├── test_api.py              # Integration test script
└── .venv/                   # Virtual environment
```

---

## 🚀 Running the App

### Start the Server
```powershell
# Activate virtual environment
.venv\Scripts\Activate.ps1

# Run FastAPI development server (auto-reload enabled)
python -m uvicorn app.main:app --reload
```

Server will be available at: **http://127.0.0.1:8000**

### Test the API
```powershell
.venv\Scripts\Activate.ps1
python test_api.py
```

---

## 🎯 Core Features

### 1️⃣ User Management
- **Register**: POST `/register` → Create new user with hashed password (Argon2)
- **Login**: POST `/login` → Returns `user_id` for dashboard access
- **No Email Verification**: Users go straight to home page after login

### 2️⃣ Song Recommendations
- **Manual Entry**: POST `/recommend/song/manual` → Add song by name
- **Photo Upload**: POST `/recommend/song/photo` → Upload image (OCR support planned)
- **Retrieve Songs**: GET `/songs/{user_id}` → Get all user songs with timestamps

### 3️⃣ Dance Workshops
- **Get All**: GET `/workshops` → List all available workshops
- **Get by City**: GET `/workshops/{city}` → Filter by location
- **Create**: POST `/workshops` → Add new workshop (city, location, date, time, style)
- **Data**: Store city, location, date, time, and dance style (salsa/bachata/kizomba/zouk)

---

## 💾 Database Schema

### `users` Table
```sql
id INTEGER PRIMARY KEY
username TEXT UNIQUE NOT NULL
password_hash TEXT NOT NULL  -- Argon2 hashed
```

### `songs` Table
```sql
id INTEGER PRIMARY KEY
user_id INTEGER (FK to users)
name TEXT
image_path TEXT (nullable)
created_at TEXT (ISO format)
```

### `workshops` Table
```sql
id INTEGER PRIMARY KEY
city TEXT
location TEXT
date TEXT (ISO format: YYYY-MM-DD)
time TEXT (HH:MM format)
style TEXT (salsa, bachata, kizomba, zouk)
```

---

## 🎨 Frontend Pages

### `index.html` - Landing Page
- Welcome banner with app description
- Links to register or login

### `register.html` - Registration
- Username & password input
- Submits to `/register` endpoint
- Redirects to login on success

### `login.html` - Login
- Username & password input
- Submits to `/login` endpoint
- Redirects to `/home.html?user_id={user_id}` on success

### `home.html` - User Dashboard
- **Navbar**: User ID display & logout button
- **Song Tab 1: Manual Entry**
  - Input field for song name
  - Submits to `/recommend/song/manual`
- **Song Tab 2: Photo Upload**
  - File picker for images
  - Submits to `/recommend/song/photo`
- **My Songs Section**: Lists all user songs with timestamps
- **Workshops Section**: Grid display of all workshops (city, location, date, time, style)

---

## 🔧 API Endpoints Summary

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/register` | Register new user |
| POST | `/login` | Login & get user_id |
| POST | `/recommend/song/manual` | Add song by name |
| POST | `/recommend/song/photo` | Upload song photo |
| GET | `/songs/{user_id}` | Get user's songs |
| GET | `/workshops` | List all workshops |
| GET | `/workshops/{city}` | Filter workshops by city |
| POST | `/workshops` | Create new workshop |
| GET | `/api/home/{user_id}` | Home endpoint (placeholder) |

---

## 📦 Dependencies

| Package | Purpose |
|---------|---------|
| `fastapi` | Web framework |
| `uvicorn` | ASGI server |
| `pydantic` | Data validation |
| `passlib[bcrypt]` | Password hashing (bcrypt fallback) |
| `argon2-cffi` | Argon2 hashing (primary) |
| `python-multipart` | Form & file upload handling |

---

## ✅ Test Results

```
📝 User Registration: ✅ (UNIQUE constraint prevents duplicates)
🔐 User Login: ✅ (Password verification works)
🎵 Add Song Manual: ✅ (Stored with timestamp)
📖 Retrieve Songs: ✅ (Returns all user songs)
🎉 Create Workshop: ✅ (Stored in database)
📍 Get Workshops: ✅ (Returns all workshops with details)
```

---

## 🔮 Next Steps / Future Enhancements

1. **Map Integration** 🗺️
   - Add Leaflet.js or Google Maps to display workshop locations
   - Show pins by city with date/time info

2. **Image to Song OCR** 📸
   - Integrate Tesseract or cloud OCR API
   - Parse song name, artist from Spotify/YouTube screenshots

3. **Session Management** 🔑
   - Add JWT tokens or secure HTTP-only cookies
   - Implement logout that invalidates sessions

4. **User Profiles** 👥
   - User bio, favorite dance styles
   - Profile picture upload

5. **Search & Filter** 🔍
   - Search songs by name, artist, style
   - Filter workshops by date range, style

6. **Admin Panel** 🛠️
   - Manage workshops (edit/delete)
   - Approve user-submitted workshops

7. **Email Notifications** 📧
   - Notify users of new workshops in their area
   - Workshop reminders

8. **Production Deployment** 🚀
   - Switch to PostgreSQL (scale beyond SQLite)
   - Deploy to Heroku, AWS, or PythonAnywhere
   - Use environment variables for secrets

---

## 🐛 Troubleshooting

**Server won't start?**
- Make sure dependencies are installed: `python -m pip install -r requirements.txt`
- Check port 8000 is not in use: `netstat -ano | findstr :8000`

**Database errors?**
- Delete `dance_app.db` to reset: `Remove-Item dance_app.db`
- Server will auto-create fresh schema on next startup

**Password hashing errors?**
- Ensure `argon2-cffi` is installed: `python -m pip install argon2-cffi`
- Use passwords under 72 bytes for safety

**Frontend not loading?**
- Check `frontend/` directory exists and has HTML files
- Ensure API endpoints respond: Visit http://127.0.0.1:8000/docs

---

## 📚 Useful Commands

```powershell
# Start server with auto-reload
python -m uvicorn app.main:app --reload

# Run tests
python test_api.py

# Interactive API docs
# Visit: http://127.0.0.1:8000/docs

# Reset database
Remove-Item dance_app.db

# Install new dependency
python -m pip install <package_name>
```

---

**Built with:** FastAPI + SQLite + HTML/CSS/JS 🎉
**Last Updated:** 2026-01-13

